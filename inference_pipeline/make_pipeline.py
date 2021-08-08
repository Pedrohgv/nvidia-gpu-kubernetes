import kfp
import kfp.components as comp
from kfp import dsl

downloader_op = comp.load_component_from_file('./download_and_extract_google_drive_op.yaml')
predict_video_metadata_op = comp.load_component_from_file('./predict_metadata_op.yaml')
'''
# prints contents of output folder form last component
check_pipeline_output_op = comp.load_component_from_file('./check_pipeline_output_op.yaml')
'''
@dsl.pipeline(name='metadata_inference_pipeline')
def metadata_inference_pipeline(tf_model_gd_id, inputs_gd_id, batch_size, score):
    
    # download model task
    download_tf_model_task = downloader_op(google_drive_id=tf_model_gd_id)
    
    # download inputs task
    download_inputs_model_task = downloader_op(google_drive_id=inputs_gd_id)


    predict_video_task = predict_video_metadata_op(
        tensorflow_model=download_tf_model_task.output,
        input_videos=download_inputs_model_task.output,
        batch_size=batch_size,
        score=score
        )
    '''
    last_op = predict_video_task
    check_pipeline_output_task = check_pipeline_output_op(previous_output_folder=last_op.output)
    '''

kfp.compiler.Compiler().compile(
    pipeline_func=metadata_inference_pipeline,
    package_path='pipeline.yaml')