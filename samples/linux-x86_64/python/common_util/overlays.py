# Copyright (c) 2019 Xnor.ai, Inc.
"""Defines the BoundingBox and Text cairo overlays

Overlays are objects that support a "draw()" method that takes a
gstreamer surface, a cairo context, a timestamp, and a duration (see
https://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good/html/gst-plugins-good-plugins-cairooverlay.html
for an explanation of the meaning of these parameters).
"""

import os

import cairo


def readable_text_color(bg_color):
    """Returns a text color which should be readable on bg_color.

    Uses BT.709 luma as an approximation of perceptual brightness, and picks a
    light or dark text color depending on the luma value.
    """
    r, g, b = bg_color
    luma709 = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if luma709 > 0.5:
        return (0.0, 0.0, 0.0)
    else:
        return (1.0, 1.0, 1.0)


class BoundingBox:
    """Bounding box overlay: a labeled rectangle at some position with some size

    `class_id` is used to determine the color of the bounding box.
    """
    LINE_WIDTH = 8

    def __init__(self, x=0, y=0, width=0, height=0, text=None,
                 bg_color=(1.0, 1.0, 1.0)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = bg_color

    def draw(self, surface, cr, timestamp, duration):
        surface_width = cr.get_target().get_width()
        surface_height = cr.get_target().get_height()

        # Transform relative positioning to absolute
        width = self.width * surface_width
        height = self.height * surface_height
        x_absolute = self.x * surface_width
        y_absolute = self.y * surface_height

        # Make space for the border
        x_rect = x_absolute + self.LINE_WIDTH
        y_rect = y_absolute + self.LINE_WIDTH

        cr.set_line_width(self.LINE_WIDTH)
        cr.set_source_rgb(*self.color)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.rectangle(x_rect, y_rect, width, height)
        cr.stroke()

        if self.text:
            self.text_overlay = Text(self.text, x_absolute, y_absolute,
                                     self.color)
            self.text_overlay.draw(surface, cr, timestamp, duration)


class FilledBox:
    """Filled box overlay: a labeled rectangle at some position with some size

    Takes same arguments as BoundingBox plus opacity
    """

    def __init__(self, x=0, y=0, width=0, height=0, text=None,
                 bg_color=(1.0, 1.0, 1.0), opacity=1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.opacity = opacity
        self.color = bg_color

    def draw(self, surface, cr, timestamp, duration):
        surface_width = cr.get_target().get_width()
        surface_height = cr.get_target().get_height()

        # Transform relative positioning to absolute
        width = self.width * surface_width
        height = self.height * surface_height
        x = self.x * surface_width
        y = self.y * surface_height

        cr.set_source_rgba(*self.color, self.opacity)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.rectangle(x, y, width, height)
        cr.fill()

        # Overlay text in the center
        if self.text:
            text_overlay = Text(self.text, x, y, self.color)
            text_overlay.draw(surface, cr, timestamp, duration)


class Text:
    """Text overlay: a string of text at some position.

    Both x and y must be absolute pixel location.
    Multi-line text is also supported by separating the lines with os.linesep.
    """
    LINE_WIDTH = BoundingBox.LINE_WIDTH
    FONT = "Courier"
    TEXT_SIZE = LINE_WIDTH * 3

    def __init__(self, text, x=0, y=0, bg_color=(0.0, 0.0, 0.0)):
        self.text = text
        self.x = x
        self.y = y
        self.background_color = bg_color
        self.text_color = readable_text_color(bg_color)

    def draw(self, surface, cr, timestamp, duration):
        # x and y store the absolute position of the upper left corner of the
        # current line.
        x = self.x + self.LINE_WIDTH
        y = self.y + self.LINE_WIDTH

        for line in self.text.split(os.linesep):
            # Write the current line at (x, y) in a group, to get the text size
            # but don't draw it yet.
            cr.push_group()
            cr.move_to(x + self.LINE_WIDTH / 2,
                       y + self.LINE_WIDTH * 1.5 + self.TEXT_SIZE / 2)
            cr.set_source_rgb(*self.text_color)
            cr.set_font_size(self.TEXT_SIZE)
            cr.select_font_face(self.FONT, cairo.FONT_SLANT_NORMAL,
                                cairo.FONT_WEIGHT_BOLD)
            cr.show_text(line)
            line_width = cr.get_current_point()[0] - x
            line_height = cr.get_current_point()[1] - y
            text_surface = cr.pop_group()

            # Draw the background rectangle first
            cr.set_source_rgb(*self.background_color)
            cr.set_line_width(2)
            cr.rectangle(x, y, line_width + self.LINE_WIDTH / 2,
                         line_height + self.LINE_WIDTH)
            cr.fill()

            # Now draw the text on top of the rectangle
            cr.set_source(text_surface)
            cr.paint()

            y += (line_height + self.LINE_WIDTH)
