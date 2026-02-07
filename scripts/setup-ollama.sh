#!/bin/bash
echo "⏳ Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Ollama is running. Pulling model..."
docker exec docqa-ollama ollama pull llama3.2
echo "✅ Model ready!"