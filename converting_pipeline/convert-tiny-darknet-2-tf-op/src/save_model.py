from absl import app, flags, logging
from absl.flags import FLAGS

def change_classes_file(folder='/darknet_model'):
    # changes config.py file to point at the correct location for the obj.names file, which contains the classes names.
    # ha to be here instead of utils.py because utils also use the cfg.YOLO.CLASSES attribute duting the import

    pattern = "__C.YOLO.CLASSES"

    file_name = './src/core/config.py'

    # reads the file and stores its contents
    with open(file_name, 'rt') as cfg_file:
        data = cfg_file.read()

    # find the line that contains the path to the obj.names
    with open(file_name, 'rt') as cfg_file:
        for line in cfg_file:
            line = line.strip('\r\n')  # it's always a good behave to strip what you read from files
            if pattern in line:
                replace_line = line
                break
    
    # replaces the entire line in the previous loaded contents of file
    data = data.replace(
        replace_line,
        "__C.YOLO.CLASSES              = " + "'" + folder  + "/config/obj.names'"
    )

    # writes to the file
    with open(file_name, 'wt') as cfg_file:
        cfg_file.write(data)

flags.DEFINE_string('input', '/darknet_model', 'folder that contains the darknet-tiny model and config folder')
flags.DEFINE_string('output', '/tf_model', 'path to where the tensorflow model will be stored')
flags.DEFINE_boolean('tiny', True, 'is yolo-tiny or not')
flags.DEFINE_integer('input_size', 416, 'define input size of export model')
flags.DEFINE_float('score_thres', 0.2, 'define score threshold')
flags.DEFINE_string('framework', 'tf', 'define what framework do you want to convert (tf, trt, tflite)')
flags.DEFINE_string('model', 'yolov4', 'yolov3 or yolov4')



def save_tf():

  # changes the config.py file to point at the right file for obj.names, according to the input folder provided in runtime
  change_classes_file(folder=FLAGS.input)

  # imports must be done inside main function because input flag arguments (and by consequence the folder containing the obj.names file)
  # are only valid inside main funtion app.
  import tensorflow as tf
  from core.yolov4 import YOLO, decode, filter_boxes
  import core.utils as utils
  from distutils.dir_util import copy_tree
  from core.config import cfg

  STRIDES, ANCHORS, NUM_CLASS, XYSCALE = utils.load_config(FLAGS)

  input_layer = tf.keras.layers.Input([FLAGS.input_size, FLAGS.input_size, 3])
  feature_maps = YOLO(input_layer, NUM_CLASS, FLAGS.model, FLAGS.tiny)
  bbox_tensors = []
  prob_tensors = []
  if FLAGS.tiny:
    for i, fm in enumerate(feature_maps):
      if i == 0:
        output_tensors = decode(fm, FLAGS.input_size // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      else:
        output_tensors = decode(fm, FLAGS.input_size // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      bbox_tensors.append(output_tensors[0])
      prob_tensors.append(output_tensors[1])
  else:
    for i, fm in enumerate(feature_maps):
      if i == 0:
        output_tensors = decode(fm, FLAGS.input_size // 8, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      elif i == 1:
        output_tensors = decode(fm, FLAGS.input_size // 16, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      else:
        output_tensors = decode(fm, FLAGS.input_size // 32, NUM_CLASS, STRIDES, ANCHORS, i, XYSCALE, FLAGS.framework)
      bbox_tensors.append(output_tensors[0])
      prob_tensors.append(output_tensors[1])
  pred_bbox = tf.concat(bbox_tensors, axis=1)
  pred_prob = tf.concat(prob_tensors, axis=1)
  if FLAGS.framework == 'tflite':
    pred = (pred_bbox, pred_prob)
  else:
    boxes, pred_conf = filter_boxes(pred_bbox, pred_prob, score_threshold=FLAGS.score_thres, input_shape=tf.constant([FLAGS.input_size, FLAGS.input_size]))
    pred = tf.concat([boxes, pred_conf], axis=-1)
  model = tf.keras.Model(input_layer, pred)
  weights = FLAGS.input + '/darknet-tiny.weights'
  utils.load_weights(model, weights, FLAGS.model, FLAGS.tiny)
  model.summary()
  model.save(FLAGS.output)

  # copies config folder provided in input to the output
  copy_tree(
    FLAGS.input + '/config',
    FLAGS.output + '/config',
    update=True
  )

def main(_argv):
  save_tf()

if __name__ == '__main__':
    try:
        app.run(main)
    except SystemExit:
        pass
