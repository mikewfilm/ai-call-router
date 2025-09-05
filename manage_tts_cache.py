#!/usr/bin/env python3
"""
Script to manage TTS cache for voice app updates
"""

import os
import shutil
import glob

def clear_tts_cache():
    """Clear all TTS cache files"""
    cache_dir = "static/tts_cache"
    
    if not os.path.exists(cache_dir):
        print("❌ TTS cache directory not found")
        return
    
    # Count files before clearing
    files_before = len(glob.glob(f"{cache_dir}/*.mp3"))
    
    # Clear all MP3 files
    for mp3_file in glob.glob(f"{cache_dir}/*.mp3"):
        os.remove(mp3_file)
        print(f"🗑️  Removed: {os.path.basename(mp3_file)}")
    
    print(f"\n✅ TTS Cache Cleared!")
    print(f"   Removed {files_before} cached audio files")
    print(f"   Next call will generate fresh audio with updated content")

def clear_specific_cache(text_type):
    """Clear specific types of cached audio"""
    cache_dir = "static/tts_cache"
    
    if not os.path.exists(cache_dir):
        print("❌ TTS cache directory not found")
        return
    
    patterns = {
        'greeting': ['*greet*', '*greeting*'],
        'hours': ['*hour*', '*time*'],
        'address': ['*address*', '*location*'],
        'phone': ['*phone*', '*call*'],
        'all': ['*.mp3']
    }
    
    if text_type not in patterns:
        print(f"❌ Unknown type: {text_type}")
        print(f"   Available types: {', '.join(patterns.keys())}")
        return
    
    removed_count = 0
    for pattern in patterns[text_type]:
        for file_path in glob.glob(f"{cache_dir}/{pattern}"):
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"🗑️  Removed: {os.path.basename(file_path)}")
                removed_count += 1
    
    print(f"\n✅ Cleared {text_type} cache!")
    print(f"   Removed {removed_count} files")

def show_cache_status():
    """Show current cache status"""
    cache_dir = "static/tts_cache"
    
    if not os.path.exists(cache_dir):
        print("❌ TTS cache directory not found")
        return
    
    mp3_files = glob.glob(f"{cache_dir}/*.mp3")
    
    print("📊 TTS Cache Status:")
    print("=" * 40)
    print(f"Total cached files: {len(mp3_files)}")
    
    if mp3_files:
        print("\n📁 Cached files:")
        for file_path in sorted(mp3_files):
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            print(f"   • {file_name} ({file_size:,} bytes)")
    else:
        print("   No cached files found")

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) < 2:
        print("🎤 TTS Cache Management")
        print("=" * 30)
        print("Usage:")
        print("  python manage_tts_cache.py clear-all     # Clear all cache")
        print("  python manage_tts_cache.py clear greeting # Clear greeting cache")
        print("  python manage_tts_cache.py clear hours   # Clear hours cache")
        print("  python manage_tts_cache.py clear address # Clear address cache")
        print("  python manage_tts_cache.py status       # Show cache status")
        return
    
    command = sys.argv[1]
    
    if command == "clear-all":
        clear_tts_cache()
    elif command == "clear" and len(sys.argv) > 2:
        clear_specific_cache(sys.argv[2])
    elif command == "status":
        show_cache_status()
    else:
        print("❌ Unknown command. Use 'python manage_tts_cache.py' for help.")

if __name__ == "__main__":
    main()
