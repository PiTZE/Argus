# 🚀 Deployment Guide - Large CSV Analytics

*"Enterprise-grade deployment for massive CSV files."*

## ⚡ Quick Setup (Development)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Application
```bash
# Copy and edit configuration
cp config.yaml config.local.yaml
# Edit database and search settings as needed
```

### 3. Add Your Data
- Put your CSV files in the `db/` directory
- Files up to 2GB each are supported
- Different column structures are fine

### 4. Run the Application
```bash
# Development mode
streamlit run main.py

# Production mode
streamlit run main.py --server.port=12000 --server.address=0.0.0.0 --server.headless=true
```

## 🐳 Docker Deployment (Recommended)

### Build and Run
```bash
# Build the image
docker build -t gharp-search .

# Run with volume mounting for data persistence
docker run -d \
  --name gharp-search \
  -p 12000:12000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/db:/app/db \
  -v $(pwd)/logs:/app/logs \
  gharp-search
```

### Docker Compose
```yaml
version: '3.8'
services:
  gharp-search:
    build: .
    ports:
      - "12000:12000"
    volumes:
      - ./data:/app/data
      - ./db:/app/db
      - ./logs:/app/logs
      - ./exports:/app/exports
    environment:
      - STREAMLIT_SERVER_PORT=12000
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: unless-stopped
```

## ◯ Production Deployment

### Environment Variables
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Docker (Optional)
*If you're into containerization:*

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

### ♄ Security Checklist
- Change the default passwords immediately
- Use HTTPS in production
- Back up your `config.yaml` file regularly
- Monitor file sizes to prevent system overload

## ⚡ Performance Optimization

### Large Files (>100MB)
- Increase system memory allocation
- Use DuckDB's external sorting for massive datasets
- Monitor disk space for temporary files

### Database Optimization
- DuckDB automatically optimizes queries
- Large files are processed in chunks
- Memory usage is monitored and limited

## ※ Troubleshooting

### Common Issues
1. **Memory errors**: Reduce file sizes or increase system memory
2. **Authentication failures**: Check `config.yaml` format and syntax
3. **Missing files**: Make sure CSV files are in the `db/` directory
4. **Slow performance**: Check file sizes and available memory

### Logs and Debugging
- Application logs are written to `streamlit.log`
- Check browser console for client-side errors
- Monitor system resources when processing large files