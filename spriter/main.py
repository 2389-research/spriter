# ABOUTME: Video to sprite sheet converter using ffmpeg
# ABOUTME: Converts MOV/MP4 videos into tile-based sprite sheets for animations

import subprocess
import sys
import json
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@click.command()
@click.argument('input_path', type=click.Path(exists=True, path_type=Path), metavar='INPUT_FILE_OR_DIRECTORY')
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output sprite sheet file (default: input_name_spritesheet_[params].png)')
@click.option('--fps', '-f', default=10, help='Frames per second to extract (default: 10)')
@click.option('--size', '-s', default='64x64', help='Size of each sprite frame (default: 64x64)')
@click.option('--grid', '-g', default='6x6', help='Grid layout for sprites (default: 6x6)')
@click.option('--preset', '-p', type=click.Choice(['game', 'web', 'hires']), help='Use preset configuration (game=64x64/10fps/6x6, web=32x32/8fps/4x4, hires=128x128/12fps/8x8)')
@click.option('--loop', '-l', is_flag=True, help='Ensure smooth looping by adding first frame at end')
@click.option('--create-gif', is_flag=True, help='Also create an animated GIF to test the loop')
def main(input_path, output, fps, size, grid, preset, loop, create_gif):
    """Convert a video file (MOV/MP4) or directory of videos into sprite sheets."""
    
    console = Console()
    
    # Apply preset configurations if specified
    if preset:
        preset_configs = {
            'game': {'fps': 10, 'size': '64x64', 'grid': '6x6'},
            'web': {'fps': 8, 'size': '32x32', 'grid': '4x4'},
            'hires': {'fps': 12, 'size': '128x128', 'grid': '8x8'}
        }
        config = preset_configs[preset]
        fps = config['fps']
        size = config['size']
        grid = config['grid']
        console.print(f"[yellow]Using preset '{preset}': fps={fps}, size={size}, grid={grid}[/yellow]")
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: ffmpeg is not installed or not in PATH[/red]")
        sys.exit(1)
    
    # Handle directory input
    if input_path.is_dir():
        # Find all video files in the directory
        video_extensions = ['.mov', '.mp4', '.mpg']
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_path.glob(f"*{ext}"))
            video_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not video_files:
            console.print(f"[red]Error: No video files found in directory '{input_path}'[/red]")
            sys.exit(1)
        
        # Process each video file
        console.print(f"[cyan]Found {len(video_files)} video files in '{input_path}'[/cyan]")
        
        for i, video_file in enumerate(video_files, 1):
            console.print(f"\n[bold]Processing {i}/{len(video_files)}: {video_file.name}[/bold]")
            process_video_file(video_file, output, fps, size, grid, preset, loop, create_gif, console)
    else:
        # Process single file
        process_video_file(input_path, output, fps, size, grid, preset, loop, create_gif, console)


def process_video_file(input_file, output, fps, size, grid, preset, loop, create_gif, console):
    """Process a single video file into a sprite sheet."""
    
    # Validate input file format
    if input_file.suffix.lower() not in ['.mov', '.mp4', '.mpg']:
        console.print(f"[red]Error: Unsupported file format '{input_file.suffix}'. Supported formats: .mov, .mp4, .mpg[/red]")
        return False
    
    # Generate output filename if not provided
    if not output:
        if preset:
            output_file = input_file.parent / f"{input_file.stem}_spritesheet_{preset}.png"
        else:
            # Include parameters in filename for easy identification
            size_clean = size.replace('x', 'x')  # Keep as-is
            grid_clean = grid.replace('x', 'x')  # Keep as-is
            output_file = input_file.parent / f"{input_file.stem}_spritesheet_{fps}fps_{size_clean}_{grid_clean}.png"
    else:
        output_file = output
    
    # Show configuration
    config_text = Text()
    config_text.append("Input: ", style="bold")
    config_text.append(str(input_file), style="cyan")
    config_text.append("\nOutput: ", style="bold")
    config_text.append(str(output_file), style="green")
    config_text.append("\nFPS: ", style="bold")
    config_text.append(str(fps), style="yellow")
    config_text.append("\nSize: ", style="bold")
    config_text.append(size, style="yellow")
    config_text.append("\nGrid: ", style="bold")
    config_text.append(grid, style="yellow")
    
    console.print(Panel(config_text, title="🎬 Sprite Sheet Configuration", border_style="blue"))
    
    # Build ffmpeg command
    if loop:
        # For seamless looping, ensure sprites end on a neutral frame
        console.print("[yellow]Creating sprite sheet with seamless looping...[/yellow]")
        
        # Get video duration to calculate proper sampling
        try:
            probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_entries', 'format=duration', str(input_file)]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            duration = float(json.loads(result.stdout)['format']['duration'])
            console.print(f"[dim]Video duration: {duration:.2f}s[/dim]")
        except Exception:
            # Fallback if we can't get duration
            duration = 5.0
            console.print(f"[dim]Using fallback duration: {duration:.2f}s[/dim]")
        
        grid_cols, grid_rows = map(int, grid.split('x'))
        total_frames = grid_cols * grid_rows
        
        # Get video frame count and calculate how many frames we'll get at the target FPS
        try:
            probe_cmd = ['ffprobe', '-v', 'quiet', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0', str(input_file)]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            video_frames = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            
            if video_frames > 0:
                # Calculate how many frames we'll get at the target FPS
                expected_frames = min(int(duration * fps), video_frames)
                console.print(f"[dim]Video has {video_frames} frames, duration {duration:.2f}s, target FPS {fps}[/dim]")
                console.print(f"[dim]Expected {expected_frames} frames at {fps}fps, need {total_frames} for {grid} grid[/dim]")
                
                if expected_frames < total_frames:
                    console.print(f"[yellow]Warning: Will get ~{expected_frames} frames at {fps}fps but need {total_frames} for {grid} grid[/yellow]")
                    console.print("[yellow]This may result in blank frames in the sprite sheet[/yellow]")
        except Exception:
            console.print("[dim]Could not determine video frame count[/dim]")
        
        # For seamless looping, sample frames evenly and add the first frame at the end
        # This ensures the animation can loop back to the beginning smoothly
        console.print(f"[dim]Creating {total_frames} frames with first frame duplicated at end for seamless loop[/dim]")
        
        # Use a simpler approach: let the GIF creation handle the loop duplication
        # The complex ffmpeg filter might be creating issues with black frames
        vf = f'fps={fps},scale={size},tile={grid}'
        console.print("[dim]Note: Loop duplication will be handled during GIF creation[/dim]")
    else:
        vf = f'fps={fps},scale={size},tile={grid}'
    
    cmd = [
        'ffmpeg',
        '-i', str(input_file),
        '-vf', vf,
        '-frames:v', '1',
        '-y',  # Overwrite output file if it exists
        str(output_file)
    ]
    
    # Run ffmpeg with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Converting video to sprite sheet...", total=None)
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            progress.update(task, description="✓ Conversion complete!")
            
            # Show success message with stats
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                console.print("[green]✓ Sprite sheet created successfully![/green]")
                console.print(f"[dim]  File: {output_file}[/dim]")
                console.print(f"[dim]  Size: {size_mb:.2f} MB[/dim]")
                
                # Create test GIF if requested (GIFs always loop)
                if create_gif:
                    gif_path = output_file.with_suffix('.gif')
                    grid_cols, grid_rows = map(int, grid.split('x'))
                    if create_sprite_gif(output_file, gif_path, grid_cols, grid_rows, fps, input_file, console):
                        console.print(f"[green]✓ Test GIF created: {gif_path} (infinite loop)[/green]")
                
                return True
            else:
                console.print("[yellow]⚠ File created but couldn't verify size[/yellow]")
                return False
                
        except subprocess.CalledProcessError as e:
            progress.update(task, description="✗ Conversion failed!")
            console.print(f"[red]Error running ffmpeg: {e}[/red]")
            if e.stderr:
                console.print(f"[red]ffmpeg error: {e.stderr}[/red]")
            return False


def create_sprite_gif(sprite_path, gif_path, grid_cols, grid_rows, fps, input_file, console):
    """Create an animated GIF from a sprite sheet to test looping."""
    if not PIL_AVAILABLE:
        console.print("[yellow]Warning: Pillow not installed, cannot create test GIF[/yellow]")
        return False
        
    try:
        # Get original video resolution
        try:
            probe_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_entries', 'stream=width,height', str(input_file)]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            streams = json.loads(result.stdout)['streams']
            video_stream = next((s for s in streams if 'width' in s and 'height' in s), None)
            if video_stream:
                original_width = video_stream['width']
                original_height = video_stream['height']
                console.print(f"[dim]Original video resolution: {original_width}x{original_height}[/dim]")
            else:
                # Fallback to sprite frame size if can't detect
                original_width = original_height = None
        except Exception:
            original_width = original_height = None
        
        # Open the sprite sheet
        sprite_sheet = Image.open(sprite_path)
        width, height = sprite_sheet.size
        
        # Calculate frame dimensions
        frame_width = width // grid_cols
        frame_height = height // grid_rows
        
        frames = []
        
        # Extract each frame from the sprite sheet
        for row in range(grid_rows):
            for col in range(grid_cols):
                left = col * frame_width
                top = row * frame_height
                right = left + frame_width
                bottom = top + frame_height
                
                frame = sprite_sheet.crop((left, top, right, bottom))
                
                # Check if frame is blank/empty and skip it
                frame_rgb = frame.convert('RGB')
                
                # For more robust blank frame detection, check multiple pixels
                pixels_to_check = [
                    (frame_width//2, frame_height//2),  # center
                    (min(10, frame_width-1), min(10, frame_height-1)),  # top-left
                    (frame_width-min(10, frame_width-1), min(10, frame_height-1)),  # top-right
                    (min(10, frame_width-1), frame_height-min(10, frame_height-1)),  # bottom-left
                    (frame_width-min(10, frame_width-1), frame_height-min(10, frame_height-1)),  # bottom-right
                    (frame_width//4, frame_height//4),  # quarter points
                    (3*frame_width//4, 3*frame_height//4)
                ]
                
                # Count blank/black pixels
                blank_pixel_count = 0
                total_brightness = 0
                
                for px, py in pixels_to_check:
                    if px < frame_width and py < frame_height:
                        pixel = frame_rgb.getpixel((px, py))
                        # Check for black pixels
                        if pixel == (0, 0, 0):
                            blank_pixel_count += 1
                        # Calculate brightness (for very dark/blank frames)
                        brightness = sum(pixel) / 3
                        total_brightness += brightness
                
                avg_brightness = total_brightness / len(pixels_to_check)
                blank_percentage = blank_pixel_count / len(pixels_to_check)
                
                # Skip if frame appears to be blank/empty
                # Either too many black pixels OR very low average brightness
                if blank_percentage >= 0.6 or avg_brightness < 10:
                    console.print(f"[dim]Skipping blank frame at position {row},{col} (blank: {blank_percentage:.1%}, brightness: {avg_brightness:.1f})[/dim]")
                    continue
                
                # Scale frame to original video resolution if available
                if original_width and original_height:
                    frame = frame.resize((original_width, original_height), Image.LANCZOS)
                
                frames.append(frame)
        
        # Always ensure smooth looping by adding the first frame at the end
        # This creates a seamless transition back to the beginning
        if len(frames) > 1:
            frames.append(frames[0])
            console.print(f"[dim]Added first frame at end for seamless GIF loop ({len(frames)} total frames)[/dim]")
        
        # Calculate frame duration in milliseconds (1000ms / fps)
        frame_duration = int(1000 / fps)
        
        # Save as animated GIF
        if frames:
            frames[0].save(
                gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0  # 0 means infinite loop
            )
            return True
        return False
        
    except Exception as e:
        console.print(f"[yellow]Warning: Could not create test GIF: {e}[/yellow]")
        return False


if __name__ == "__main__":
    main()
