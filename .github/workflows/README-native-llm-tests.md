# Native LLM Tests Workflow

This workflow runs native LLM tests using models downloaded from various sources.

## Features

- **Multiple Model Sources**: Supports downloading models from:
  - Direct URL via `CI_MODEL_URL` secret
  - AWS S3 via `CI_MODEL_S3_BUCKET` and `CI_MODEL_S3_KEY` secrets
  - Google Cloud Storage via `CI_MODEL_GCS_BUCKET` and `CI_MODEL_GCS_OBJECT` secrets
  - GitHub Actions artifact named `model-gguf-artifact`

- **Conditional Execution**: Automatically skips when no model sources are configured
- **Source Reporting**: Outputs which source was used via `steps.get_model.outputs.model_source`

## Configuration

### Using Direct URL

Set the `CI_MODEL_URL` secret to a direct download URL for your GGUF model:

```
CI_MODEL_URL = https://example.com/path/to/model.gguf
```

### Using AWS S3

Set the following secrets:

```
CI_MODEL_S3_BUCKET = my-bucket-name
CI_MODEL_S3_KEY = path/to/model.gguf
AWS_ACCESS_KEY_ID = your-access-key
AWS_SECRET_ACCESS_KEY = your-secret-key
AWS_DEFAULT_REGION = us-east-1  # optional
```

### Using Google Cloud Storage

Set the following secrets:

```
CI_MODEL_GCS_BUCKET = my-bucket-name
CI_MODEL_GCS_OBJECT = path/to/model.gguf
GOOGLE_APPLICATION_CREDENTIALS = <JSON service account key>
```

### Using GitHub Artifact

Upload an artifact in a previous job with the name `model-gguf-artifact` containing your model file.

## Model Requirements

- Models must be in GGUF format
- Minimum file size: 100MB
- Recommended: Use quantized models (Q4_K_M or similar) for faster CI runs

## Testing Locally

To test the workflow locally without committing:

1. Install dependencies: `pip install -r requirements.txt llama-cpp-python`
2. Download a model to `models/tinyllama/model.gguf`
3. Run: `python scripts/test_local_inference.py --model tinyllama --quick`

## Troubleshooting

- **Workflow skipped**: No model sources configured - this is expected behavior
- **Download fails**: Check that secrets are correctly set and credentials have proper permissions
- **Model too small**: Ensure you're downloading a complete GGUF model file (not a placeholder)
