// Copyright (c) 2019 Xnor.ai, Inc.
//
// This sample runs a classification model over an input jpeg and prints out the
// resulting classified object.
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

// Returns the name of the most prominent object in the image, using deep
// learning.
bool identify_jpeg_using_xnornet(const char* filename, char** label_out);

int main(int argc, char* argv[]) {
  if (argc != 2 || argv[1][0] == '-') {
    fprintf(stderr, "Usage: %s <image.jpg>\n", argv[0]);
    return EXIT_FAILURE;
  }

  char* label = NULL;
  if (!identify_jpeg_using_xnornet(argv[1], &label)) {
    return EXIT_FAILURE;
  }

  fputs("This looks like... ", stdout);

  if (label == NULL) {
    puts("something unfamiliar!");
  } else {
    puts(label);
  }

  free(label);

  return EXIT_SUCCESS;
}

bool identify_jpeg_using_xnornet(const char* image_filename,
                                 char** label_out) {
  // Make sure we got a JPEG
  const char* image_ext = strrchr(image_filename, '.');
  if (image_ext == NULL ||
      (strcasecmp(image_ext, ".jpg") != 0 &&
       strcasecmp(image_ext, ".jpeg") != 0)) {
    fprintf(stderr, "Sorry, this demo only supports jpeg images!\n");
    return false;
  }

  // Read the JPEG into memory
  uint8_t* jpeg_data;
  int32_t data_size;
  if (!read_entire_file(image_filename, &jpeg_data, &data_size)) {
    fprintf(stderr, "Couldn't read data from %s!\n", image_filename);
    return false;
  }

  // Create the input handle for the Xnornet model.
  xnor_error* error = NULL;
  xnor_input* input = NULL;
  if ((error = xnor_input_create_jpeg_image(jpeg_data, data_size,
                                            &input)) != NULL) {
    fputs(xnor_error_get_description(error), stderr);
    free(jpeg_data);
    return false;
  }

  // Initialize the Xnornet model
  xnor_model* model = NULL;
  if ((error = xnor_model_load_built_in("", NULL, &model)) != NULL) {
    fputs(xnor_error_get_description(error), stderr);
    free(jpeg_data);
    return false;
  }

  // Evaluate the model! (The model looks for known objects in the image, using
  // deep learning)
  xnor_evaluation_result* result = NULL;
  if ((error = xnor_model_evaluate(model, input, NULL, &result)) != NULL) {
    fputs(xnor_error_get_description(error), stderr);
    free(jpeg_data);
    return false;
  }

  // Don't need to keep around the image data any more, now that the model has
  // used it.
  xnor_input_free(input);
  free(jpeg_data);

  // And, since we're done evaluating the model, free the model too
  xnor_model_free(model);

  // Check what kind of model this is by investigating the kind of results it
  // returned.
  // A Classification model will always return zero or more Class Labels
  if (xnor_evaluation_result_get_type(result) !=
      kXnorEvaluationResultTypeClassLabels) {
    fputs("Oops! I wasn't linked with a classification model!\n", stderr);
    return false;
  }

  // Now we can get the specific class labels involved as a string and pass it
  // back to the calling code!
  xnor_class_label label;
  int32_t num_labels =
      xnor_evaluation_result_get_class_labels(result, &label, 1);

  if (num_labels > 0) {
    // Use strdup here because the label string will be deallocated when we call
    // xnor_evaluation_result_free()
    *label_out = strdup(label.label);
  }

  xnor_evaluation_result_free(result);
  return true;
}
