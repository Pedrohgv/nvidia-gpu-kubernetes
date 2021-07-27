This is a Kubeflow training pipeline. Each folder is a containerized Kubeflow component that is reusable and is represented by a `component.yaml` file. The `component.yaml` file describes the container image used by that component; for custom images, the component folder also contains the `Dockerfile` and the source files for that image.