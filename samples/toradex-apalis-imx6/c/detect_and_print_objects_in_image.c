// Copyright (c) 2019 Xnor.ai, Inc.
//
// This sample runs a detection model over an input jpeg and prints out the
// resulting detected object.
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// File-loading helpers
#include "common_util/file.h"
// Definitions for the Xnor model API
#include "xnornet.h"

// Maximum number of objects to report in a scene
#define MAX_OBJECTS 10

#define min(x, y) (((x) < (y)) ? (x) : (y))

// Returns bounding boxes around all of the recognized objects in an image using
// Deep Learning.
xnor_evaluation_result* detect_objects_in_jpeg_using_xnornet(
    const char* image_filename, xnor_bounding_box* objects_out,
    int32_t objects_out_size);

int main(int argc, char* argv[]) {
  if (argc != 2) {
    fprintf(stderr, "Usage: %s <image.jpg>\n", argv[0]);
    return EXIT_FAILURE;
  }

  xnor_evaluation_result* result;
  xnor_bounding_box objects[MAX_OBJECTS] = {0};
  if ((result = detect_objects_in_jpeg_using_xnornet(argv[1], objects,
                                                     MAX_OBJECTS)) == NULL) {
    return EXIT_FAILURE;
  }

  int32_t num_objects =
      xnor_evaluation_result_get_bounding_boxes(result, NULL, 0);

  puts("In this image, there's: ");

  if (num_objects == 0) {
    puts("nothing recognizable!");
  }

  for (int32_t i = 0; i < min(num_objects, MAX_OBJECTS); ++i) {
    printf("  %s\n", objects[i].class_label.label);
  }

  xnor_evaluation_result_free(result);

  return EXIT_SUCCESS;
}

xnor_evaluation_result* detect_objects_in_jpeg_using_xnornet(
    const char* image_filename, xnor_bounding_box* objects_out,
    int32_t objects_out_size) {
  // Make sure we got a JPEG
  const char* image_ext = strrchr(image_filename, '.');
  if (strcasecmp(image_ext, ".jpg") != 0 &&
      strcasecmp(image_ext, ".jpeg") != 0) {
    fprintf(stderr, "Sorry, this demo only supports jpeg images!\n");
    return NULL;
  }

  // Read the JPEG into memory
  uint8_t* jpeg_data;
  int32_t data_size;
  if (!read_entire_file(image_filename, &jpeg_data, &data_size)) {
    fprintf(stderr, "Couldn't read data from %s!\n", image_filename);
    return NULL;
  }

  // Create the input handle for the Xnornet model.
  xnor_error* error = NULL;
  xnor_input* input = NULL;
  if ((error = xnor_input_create_jpeg_image(jpeg_data, data_size,
                                            &input)) != NULL) {
    fputs(xnor_error_get_description(error), stderr);
    free(jpeg_data);
    return NULL;
  }

  // Initialize the Xnornet model
  xnor_model* model = NULL;
  if ((error = xnor_model_load_built_in("", NULL, &model)) != NULL) {
    fputs(xnor_error_get_description(error), stderr);
    free(jpeg_data);
    return NULL;
  }

  // Evaluate the model! (The model looks for known objects in the image, using
  // deep learning)
  xnor_evaluation_result* result = NULL;
  if ((error = xnor_model_evaluate(model, input, NULL, &result)) != NULL) {
    fputs(xnor_error_get_description(error), stderr);
    free(jpeg_data);
    return NULL;
  }

  // Don't need to keep around the image data any more, now that the model has
  // used it.
  xnor_input_free(input);
  free(jpeg_data);

  // And, since we're done evaluating the model, free the model too
  xnor_model_free(model);

  // Check what kind of model this is by investigating the kind of results it
  // returned.
  // An Object Detection model will always return zero or more Bounding Boxes
  if (xnor_evaluation_result_get_type(result) !=
      kXnorEvaluationResultTypeBoundingBoxes) {
    fputs("Oops! I wasn't linked with an object detection model!\n", stderr);
    xnor_evaluation_result_free(result);
    return NULL;
  }

  xnor_evaluation_result_get_bounding_boxes(result, objects_out,
                                            objects_out_size);

  return result;
}
