#!/bin/bash
# Type checking script using pyright

echo "🔍 Running type checking with pyright..."
echo "=" * 50

uv run pyright

if [ $? -eq 0 ]; then
    echo "✅ Type checking passed!"
else
    echo "❌ Type checking failed. Please fix the issues above."
    exit 1
fi
