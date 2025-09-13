#!/bin/bash
# Log Rotation and Cleanup Script
# Generated on 2025-08-04T17:45:58.976571

LOGS_DIR="logs"
ARCHIVE_DIR="$LOGS_DIR/archived"
RETENTION_DAYS=7
CLEANUP_DAYS=30

echo "🔄 Starting log rotation and cleanup..."

# Create directories if they don't exist
mkdir -p "$LOGS_DIR/freqtrade" "$LOGS_DIR/web_ui" "$LOGS_DIR/system" "$ARCHIVE_DIR"

# Archive old logs (older than $RETENTION_DAYS days)
echo "📦 Archiving logs older than $RETENTION_DAYS days..."
find "$LOGS_DIR" -name "*.log" -type f -mtime +$RETENTION_DAYS -not -path "$ARCHIVE_DIR/*" -exec mv {} "$ARCHIVE_DIR/" \;

# Clean up very old archived logs (older than $CLEANUP_DAYS days)
echo "🧹 Cleaning up archived logs older than $CLEANUP_DAYS days..."
find "$ARCHIVE_DIR" -name "*.log" -type f -mtime +$CLEANUP_DAYS -delete

# Compress large log files
echo "🗜️  Compressing large log files..."
find "$LOGS_DIR" -name "*.log" -type f -size +10M -exec gzip {} \;

echo "✅ Log rotation and cleanup completed!"

# Show current log directory size
echo "📊 Current logs directory size:"
du -sh "$LOGS_DIR"
