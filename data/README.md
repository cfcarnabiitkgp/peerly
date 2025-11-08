# Persistent Data Directory

This directory contains persistent data for Docker services.

## Structure

```
data/
└── qdrant/          # Qdrant vector database storage
    └── storage/     # Auto-created by Qdrant container
        ├── collections/
        ├── snapshots/
        └── raft/
```

## Qdrant Storage

The `qdrant/` directory is mounted as a volume in the Qdrant Docker container. This ensures:

- **Persistence**: Vector embeddings survive container restarts
- **Durability**: Data is not lost when updating containers
- **Portability**: Easy to backup, migrate, or version control (if needed)

### Collections Stored Here

- `clarity_guidelines`: Embeddings for clarity-focused writing guidelines
- `rigor_guidelines`: Embeddings for mathematical rigor guidelines

### Backup

To backup your embeddings:

```bash
# Create a backup
tar -czf qdrant-backup-$(date +%Y%m%d).tar.gz data/qdrant/

# Restore from backup
tar -xzf qdrant-backup-YYYYMMDD.tar.gz
```

### Reset

To completely clear all vector data:

```bash
./scripts/reset-qdrant.sh
```

This will:
1. Stop Qdrant container
2. Remove all collections and embeddings
3. Clear the `data/qdrant/` directory
4. Optionally clear embedding cache

After resetting, re-run the embedding script:

```bash
python scripts/embed_documents.py --all
```

## Git Ignore

The contents of `data/qdrant/` are excluded from version control via `.gitignore`.

This is intentional because:
- Vector embeddings are large binary files
- They can be regenerated from source PDFs
- Cloud deployments use different storage mechanisms

## Cloud Deployments

### Railway
- Use Railway Volumes: https://docs.railway.app/reference/volumes
- Mount to `/qdrant/storage` in the container

### AWS ECS
- Use Amazon EFS (Elastic File System)
- Mount to task definition volume

### Azure
- Use Azure Files
- Configure in container instance YAML

### Google Cloud
- Use persistent disks or Cloud Storage FUSE
- Mount to container spec

See `docker-compose.yml` for cloud deployment notes.
