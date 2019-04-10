# Copyright (c) 2019 Xnor.ai, Inc.

"""Utility class that manages a GStreamer pipeline and GTK window.

The pipeline can be started either from a webcam or a video file. It supports
adding any number of overlays to the final composited image in the window (see
overlays.py)
"""

import collections
import ctypes
import logging
import threading

import gi
gi.require_foreign('cairo')
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gdk
from gi.repository import GdkX11
from gi.repository import GObject
from gi.repository import Gst
from gi.repository import GstApp
from gi.repository import GstVideo
from gi.repository import Gtk

Frame = collections.namedtuple("Frame", ["format", "size", "data"])
Frame.__doc__ = """\
A single frame of video (an image buffer).
- `format`: a string describing the format of the buffer (e.g. "RGB")
- `size`: A tuple of image dimensions, (w, h)
- `data': A `bytes` object with the image data in the given format
"""
Frame.__repr__ = lambda self: "Frame ({}, {}x{})".format(
    self.format, *self.size)

LOG = logging.getLogger(__name__)


# Helper to deal with an inconsistency in pygobject's gstreamer bindings across
# versions
def _gst_buffer_extract(buf):
    """Return a bytes containing the same data as @buf"""
    # We would like to use Gst.Buffer.extract_dup, buf in certain older versions
    # of pygobject, it leaks memory by not cleaning up after marshalling the
    # returned data into a python Bytes. So instead we have to use
    # Gst.Buffer.extract, which copies into a caller-allocated array.
    #
    # ca. Mar 2018 gstreamer was updated to include proper introspection
    # annotations on gst_buffer_extract -- before this, it had to be called with
    # a C pointer even in Python.
    if Gst.Buffer.extract.get_arguments()[1].is_caller_allocates():
        # After the change, Gst.Buffer.extract now segfaults. Luckily, the
        # memory leak was fixed around the same time as the introspection
        # annotations were updated, so this is probably okay.
        return buf.extract_dup(0, buf.get_size())
    else:
        # Get the sample image data as a python Bytes via ctypes
        image_data = ctypes.create_string_buffer(buf.get_size())
        data_ptr = ctypes.cast(image_data, ctypes.c_void_p).value
        buf.extract(0, data_ptr, buf.get_size())
        return image_data.raw


class GStreamerPipeline(Gtk.Window):
    """An abstract GStreamer pipeline.

    This shouldn't be constructed directly. Instead it should be subclassed to
    instantiate particular pipelines that wire together components in different
    ways.
    """

    def __init__(self, window_title, webcam_device=None, video_input=None):
        GObject.threads_init()
        Gst.init(None)
        super().__init__()

        # Implementation-specific pipeline (handled in concrete classes).
        self._build_pipeline(webcam_device, video_input)

        # Implementation pipeline must have created an appsink for get_frame to
        # operate correctly
        if self._appsink is None:
            raise ValueError("appsink must be valid!")

        # Hook up some useful signals
        # We want to be notified when the pipeline state changes, and when the
        # video sink is ready to draw (the sync message). So we enable both
        # kinds of signals and set our handlers.
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self._on_message)
        bus.connect("sync-message::element", self._on_sync_message)

        # Makes sure we're not polling for frames while the pipeline stops
        self._pipeline_lock = threading.Lock()

        # Configure the window properties
        self.set_title(window_title)
        self.set_default_size(1280, 960)
        # Register ourselves for keyboard events, so we can pause, stop, etc.
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key-press-event", self._on_key_press_event)
        self.connect("destroy", self.stop)

        # Keep track of whether we are started or stopped
        self.running = False

    def __enter__(self):
        """Pipelines are themselves context objects which manage the gstreamer
        resources. Start the pipeline.
        """

        self.start()
        return self

    def __exit__(self, type, value, traceback):
        """Pipelines are themselves context objects which manage the gstreamer
        resources. Stop the pipeline and propagate any exception.
        """

        self.stop()
        return

    def _build_pipeline(self, webcam_device, video_input):
        """Subclasses should provide implementations of this method."""
        raise NotImplementedError()

    def _on_message(self, bus, message):
        """GStreamer callback for processing stream status messages"""
        if message.type == Gst.MessageType.EOS:
            self.stop()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            LOG.error("GStreamer error: {}. {}".format(err, debug))
            self.stop()
        return True

    def _on_sync_message(self, bus, message):
        """GStreamer callback for processing stream synchronization messages"""
        if message.get_structure().get_name() == "prepare-window-handle":
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_window_handle(self.get_property("window").get_xid())

    def _on_key_press_event(self, widget, key_event):
        """GTK callback for processing window key event messages"""
        if (key_event.keyval == Gdk.KEY_Escape or
                key_event.keyval == Gdk.KEY_q or key_event.keyval == Gdk.KEY_Q):
            self.stop()
        elif (key_event.keyval == Gdk.KEY_p or
              key_event.keyval == Gdk.KEY_space):
            self.toggle_pause()
        return True

    def _make_element(self, type, name):
        """Create a single GStreamer element and add it to this class's pipeline

        Refer to the GStreamer docs for a list of the available element types:
        https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-base-plugins/html/
        """
        element = Gst.ElementFactory.make(type, name)
        if not element:
            raise CreateFailure(name)
        self._pipeline.add(element)
        return element

    def _link(self, src, dest, message_formatter=None):
        """Link src to dest, raising an error if the linkage fails"""
        if not src.link(dest):
            raise LinkFailure(src, dest, message_formatter)

    def _make_local_webcam_source(self, device_name=None):
        """Create the GStreamer elements necessary to source from a local webcam
        """
        v4l2src = self._make_element('v4l2src', 'source_v4l2src')
        if device_name is not None:
            v4l2src.props.device = device_name
        capsfilter = self._make_element('capsfilter', 'source_capsfilter')
        caps_settings = "image/jpeg,framerate=[10/1,30/1],width=[640,1280]"
        capsfilter.props.caps = Gst.Caps.from_string(caps_settings)
        jpegdecoder = self._make_element('jpegdec', 'source_jpegdec')
        self._link(v4l2src, capsfilter)
        self._link(capsfilter, jpegdecoder)
        return jpegdecoder

    def _make_video_input_source(self, video_input):
        """Create the GStreamer elements necessary to source from a video file

        Can be local or a remote URI.
        """
        if video_input.find("://") != -1:
            video_src = self._make_element("uridecodebin", "source_uridecode")
            video_src.props.uri = video_input
            source_element = video_src
        else:
            video_src = self._make_element("filesrc", "source_file")
            video_src.props.location = video_input
            decoder = self._make_element("decodebin", "source_decode")
            self._link(video_src, decoder)
            source_element = decoder

        # The above elements don't have any concrete pads available until they
        # infer their input type from the file / stream, so create a video
        # converter source and have them dynamically link to it once the pads
        # are enumerated
        converter = self._make_element("videoconvert", "source_convert")

        def on_no_more_pads(element, self, converter):
            self._link(element, converter)
        source_element.connect("no-more-pads", on_no_more_pads, self, converter)
        return converter

    def _make_video_source(self, webcam_device, video_input):
        """Create either a video source or a webcam source

        Creates only a video file source if both are specified.
        Creates a webcam source on the first available webcam if neither are
        specified.
        """
        if video_input is not None:
            source = self._make_video_input_source(video_input)
        else:
            source = self._make_local_webcam_source(webcam_device)
        return source

    def _make_appsink(self):
        """Creates an appsink suitable for capturing RGB frames from the source
        """
        queue = self._make_element('queue', 'appsink_queue')
        queue.props.max_size_buffers = 1
        converter = self._make_element('videoconvert', 'appsink_converter')
        capsfilter = self._make_element('capsfilter', 'appsink_capsfilter')
        capsfilter.props.caps = Gst.Caps.from_string('video/x-raw,format=RGB')
        appsink = self._make_element('appsink', 'appsink')
        appsink.props.max_buffers = 1
        appsink.props.drop = True  # Drop old buffers when queue is full
        self._link(queue, converter)
        self._link(converter, capsfilter)
        self._link(capsfilter, appsink)
        self._appsink = appsink
        return queue

    def _make_auto_sink(self):
        """Creates an automatic sink that displays video to the screen"""
        converter = self._make_element('videoconvert', 'auto_sink_converter')
        sink = self._make_element('autovideosink', 'auto_sink')
        self._link(converter, sink)
        return converter

    def _set_state(self, state):
        """Internal helper that sets the pipeline state to a Gst.State"""
        ret = self._pipeline.set_state(state)
        if ret == Gst.StateChangeReturn.FAILURE:
            raise StateChangeFail(state)

    def _get_state(self):
        """Internal helper that gets the current pipeline Gst.State"""
        _, cur_state, _ = self._pipeline.get_state(Gst.SECOND)
        return cur_state

    ############################
    # Start of public class API
    ############################

    def get_frame(self):
        """Block until a frame is available, then return it as a Frame."""
        # Refuse to do anything if stop() has been called
        if not self.running:
            LOG.warning("Tried to get a frame from a stopped pipeline!")
            return None

        # Process GTK events so that the window keeps updating
        # Doing this instead of calling Gtk.main_loop() allows us to evaluate
        # the model on the main thread
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

        # Get a sample from the pipeline
        _, cur_state, _ = self._pipeline.get_state(Gst.SECOND)
        if cur_state == Gst.State.PLAYING:
            with self._pipeline_lock:
                gst_sample = self._appsink.pull_sample()
        elif cur_state == Gst.State.PAUSED:
            with self._pipeline_lock:
                gst_sample = self._appsink.pull_preroll()
        else:
            LOG.info("Video pipeline is not playing; no frame to return")
            return None

        if gst_sample is None:
            LOG.warning("Could not pull sample")
            return None

        data = gst_sample.get_buffer()
        # Get the sample metadata
        caps_struct = gst_sample.get_caps().get_structure(0)
        frame_format = caps_struct.get_string('format')
        frame_size = (caps_struct.get_value('width'),
                      caps_struct.get_value('height'))

        image_data = _gst_buffer_extract(data)
        return Frame(frame_format, frame_size, image_data)

    def play(self):
        """Resume the GStreamer pipeline"""
        self._set_state(Gst.State.PLAYING)

    def toggle_pause(self):
        """Toggle whether the GStreamer pipeline is playing or paused"""
        cur_state = self._get_state()
        if (cur_state == Gst.State.PLAYING):
            self._set_state(Gst.State.PAUSED)
        elif (cur_state == Gst.State.PAUSED):
            self._set_state(Gst.State.PLAYING)

    def start(self):
        """Kick off the video pipeline and open the window"""
        LOG.info("Starting video pipeline")
        self.play()
        self.show_all()
        self.running = True

    def stop(self, widget=None):
        """Stop the GStreamer pipeline and close the window"""
        with self._pipeline_lock:
            self._set_state(Gst.State.NULL)
            self.hide()
            self.running = False


class VideoOverlayPipeline(GStreamerPipeline):
    """A pipeline that can draw overlays on top of live-streaming video

    Uses a cairo overlay element to asynchronously update the video overlay at a
    different framerate from the underlying video.
    """

    def __init__(self, window_title, webcam_device=None, video_input=None):
        super().__init__(window_title, webcam_device, video_input)

        self._overlays = []
        self._overlays_lock = threading.Lock()

    def _make_overlay(self):
        """Creates a cairo overlay element and hooks up the draw signal"""
        queue = self._make_element('queue', 'overlay_queue')
        queue.props.max_size_buffers = 1
        converter = self._make_element('videoconvert', 'overlay_converter')
        overlay = self._make_element('cairooverlay', 'overlay')
        overlay.connect('draw', self._draw_overlays)
        self._link(queue, converter)
        self._link(converter, overlay)
        return queue, overlay

    def _build_pipeline(self, webcam_device, video_input):
        """Constructs the video overlay pipeline"""
        pipeline = Gst.Pipeline.new('video-overlay-pipeline')
        if not pipeline:
            raise CreateFailure('video-overlay-pipeline')
        self._pipeline = pipeline

        source = self._make_video_source(webcam_device, video_input)
        tee_no_overlay = self._make_element('tee', 'tee_no_overlay')
        appsink = self._make_appsink()
        overlay_in, overlay_out = self._make_overlay()
        auto_sink = self._make_auto_sink()

        self._link(source, tee_no_overlay)
        self._link(tee_no_overlay, appsink)
        self._link(tee_no_overlay, overlay_in)
        self._link(overlay_out, auto_sink)

    def _draw_overlays(self, surface, cr, timestamp, duration):
        """GStreamer callback for drawing our overlays to the cairooverlay"""
        with self._overlays_lock:
            for overlay in self._overlays:
                overlay.draw(surface, cr, timestamp, duration)

    ############################
    # Start of public class API
    ############################

    def remove_overlay(self, overlay):
        """Remove a particular overlay from the window

        If overlay was not previously added, or has already been
        removed/cleared, an exception will be thrown.
        """
        with self._overlays_lock:
            self._overlays.remove(overlay)

    def add_overlay(self, overlay):
        """Add an overlay to the window

        The overlay will be drawn every tick of the GStreamer pipeline until
        removed or cleared.
        """
        with self._overlays_lock:
            self._overlays.append(overlay)

    def clear_overlay(self):
        """Clear all overlays (bounding boxes and text) from the window."""
        with self._overlays_lock:
            self._overlays.clear()


class VideoProcessingPipeline(GStreamerPipeline):

    def __init__(self, window_title, webcam_device=None, video_input=None):
        super().__init__(window_title, webcam_device, video_input)

        # Make sure the appsrc was created successfully for put_frame
        if self._appsrc is None:
            raise ValueError("appsink must be valid!")

        # Makes sure we're not polling for frames while the pipeline stops
        self._pipeline_lock = threading.Lock()

    def _make_appsrc(self):
        self._appsrc = self._make_element('appsrc', 'appsrc')
        self._appsrc.set_stream_type(GstApp.AppStreamType.STREAM)
        return self._appsrc

    def _build_pipeline(self, webcam_device, video_input):
        pipeline = Gst.Pipeline.new('video-processing-pipeline')
        if not pipeline:
            raise CreateFailure('video-processing-pipeline')
        self._pipeline = pipeline

        source = self._make_video_source(webcam_device, video_input)
        appsink_queue = self._make_appsink()
        appsrc = self._make_appsrc()
        autosink = self._make_auto_sink()

        self._link(source, appsink_queue)
        self._link(appsrc, autosink)

    ############################
    # Start of public class API
    ############################

    def put_frame(self, processed_frame):
        processed_width, processed_height = processed_frame.size

        # Push the frame to the appsrc
        buf = Gst.Buffer.new_wrapped(processed_frame.data)
        caps_struct = Gst.Structure.new_empty('video/x-raw')
        caps_struct.set_value("format", processed_frame.format)
        caps_struct.set_value("width", processed_width)
        caps_struct.set_value("height", processed_height)
        frame_caps = Gst.Caps.new_empty()
        frame_caps.append_structure(caps_struct)
        self._appsrc.set_caps(frame_caps)

        self._appsrc.push_buffer(buf)


class CreateFailure(Exception):

    def __str__(self):
        return 'Failed to create element {}'.format(self.args[0])


class LinkFailure(Exception):

    def __init__(self, src, sink, message_formatter=None):
        if message_formatter is None:
            message_formatter = 'ERROR: Failed to link elements {src} -> {dest}'
        super().__init__(message_formatter.format(src=src.name, dest=sink.name))


class StateChangeFail(Exception):

    def __init__(self, state):
        super().__init__('ERROR: Unable to set pipeline to state {}'.format(
            state.value_name))
