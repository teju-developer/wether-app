"""
Icon Generator for SkyPulse Weather Dashboard.
Renders high-definition, anti-aliased weather illustrations and icons using Pillow.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = Path(__file__).resolve().parent / "weather_icons"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_base_canvas(size: int = 160) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create a transparent RGBA image and draw context with supersampling."""
    # Render at 2x resolution for clean anti-aliasing then downscale
    upscale = size * 2
    img = Image.new("RGBA", (upscale, upscale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    return img, draw


def finalize(img: Image.Image, filename: str, target_size: int = 160):
    """Downsample with Lanczos resampling and save."""
    out = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    out.save(OUTPUT_DIR / filename, "PNG")


def draw_sun(draw, center_x, center_y, radius, color=(255, 193, 7, 255), ray_color=(255, 213, 79, 230)):
    """Draw a radiant sun with beams."""
    # Rays
    ray_count = 8
    ray_len = radius * 0.45
    for i in range(ray_count):
        angle = i * (2 * math.pi / ray_count)
        x1 = center_x + (radius + 4) * math.cos(angle)
        y1 = center_y + (radius + 4) * math.sin(angle)
        x2 = center_x + (radius + 4 + ray_len) * math.cos(angle)
        y2 = center_y + (radius + 4 + ray_len) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=ray_color, width=max(4, int(radius * 0.16)))

    # Glow circle
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=color
    )
    # Inner highlight
    inner_r = radius * 0.8
    draw.ellipse(
        [center_x - inner_r, center_y - inner_r, center_x + inner_r * 0.6, center_y + inner_r * 0.6],
        fill=(255, 238, 88, 120)
    )


def draw_moon(draw, center_x, center_y, radius, color=(226, 232, 240, 255)):
    """Draw a luminous crescent moon with stars."""
    # Main moon sphere
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=color
    )
    # Subtract mask
    offset_x = center_x + radius * 0.45
    offset_y = center_y - radius * 0.25
    cut_r = radius * 0.88
    draw.ellipse(
        [offset_x - cut_r, offset_y - cut_r, offset_x + cut_r, offset_y + cut_r],
        fill=(0, 0, 0, 0)
    )
    # Twinkling stars
    star_positions = [
        (center_x + radius * 0.8, center_y - radius * 0.6, 6),
        (center_x + radius * 1.1, center_y + radius * 0.1, 4),
        (center_x - radius * 0.7, center_y + radius * 0.8, 5),
    ]
    for sx, sy, sr in star_positions:
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 255, 255, 220))


def draw_cloud(draw, x, y, width, height, color=(226, 232, 240, 240), highlight=(255, 255, 255, 180)):
    """Draw a modern stylized cumulus cloud."""
    # Bottom pill base
    base_h = height * 0.45
    draw.rounded_rectangle(
        [x, y + height - base_h, x + width, y + height],
        radius=base_h / 2,
        fill=color
    )
    # Left puff
    puff1_r = height * 0.38
    draw.ellipse(
        [x + width * 0.12, y + height - puff1_r * 2 - 4, x + width * 0.12 + puff1_r * 2, y + height - 4],
        fill=color
    )
    # Central tall puff
    puff2_r = height * 0.52
    draw.ellipse(
        [x + width * 0.32, y + height - puff2_r * 2, x + width * 0.32 + puff2_r * 2, y + height],
        fill=color
    )
    # Right puff
    puff3_r = height * 0.4
    draw.ellipse(
        [x + width * 0.55, y + height - puff3_r * 2 - 6, x + width * 0.55 + puff3_r * 2, y + height - 6],
        fill=color
    )
    # Soft highlight on top puff
    draw.ellipse(
        [x + width * 0.36, y + height - puff2_r * 2 + 6, x + width * 0.36 + puff2_r * 1.4, y + height - puff2_r * 1.2],
        fill=highlight
    )


def generate_all_icons():
    """Generate all application icons and save to disk."""
    scale = 320  # 2x supersampling for 160x160 base

    # 1. Clear Day
    img, draw = create_base_canvas(160)
    draw_sun(draw, 160, 160, 65)
    finalize(img, "clear_day.png")

    # 2. Clear Night
    img, draw = create_base_canvas(160)
    draw_moon(draw, 150, 160, 65)
    finalize(img, "clear_night.png")

    # 3. Few Clouds Day
    img, draw = create_base_canvas(160)
    draw_sun(draw, 210, 110, 48)
    draw_cloud(draw, 40, 140, 240, 120)
    finalize(img, "few_clouds_day.png")

    # 4. Few Clouds Night
    img, draw = create_base_canvas(160)
    draw_moon(draw, 210, 110, 45)
    draw_cloud(draw, 40, 140, 240, 120, color=(148, 163, 184, 230))
    finalize(img, "few_clouds_night.png")

    # 5. Cloudy
    img, draw = create_base_canvas(160)
    # Back dark cloud
    draw_cloud(draw, 30, 90, 200, 100, color=(100, 116, 139, 210))
    # Front bright cloud
    draw_cloud(draw, 60, 135, 230, 115, color=(203, 213, 225, 255))
    finalize(img, "cloudy.png")

    # 6. Rain
    img, draw = create_base_canvas(160)
    draw_cloud(draw, 45, 80, 230, 110, color=(148, 163, 184, 250))
    # Raindrops
    rain_x = [90, 130, 170, 210, 245]
    for rx in rain_x:
        draw.line([(rx, 210), (rx - 16, 260)], fill=(56, 189, 248, 240), width=6)
    finalize(img, "rain.png")

    # 7. Heavy Rain
    img, draw = create_base_canvas(160)
    draw_cloud(draw, 40, 75, 240, 115, color=(71, 85, 105, 255))
    # Dense Raindrops
    rain_x = [75, 110, 145, 180, 215, 250]
    for rx in rain_x:
        draw.line([(rx, 205), (rx - 20, 265)], fill=(14, 165, 233, 255), width=7)
    finalize(img, "heavy_rain.png")

    # 8. Thunderstorm
    img, draw = create_base_canvas(160)
    draw_cloud(draw, 40, 70, 240, 115, color=(51, 65, 85, 255))
    # Lightning bolt
    bolt = [
        (165, 185), (140, 230), (160, 230),
        (130, 285), (185, 225), (160, 225), (180, 185)
    ]
    draw.polygon(bolt, fill=(250, 204, 21, 255))
    # Drops
    for rx in [85, 235]:
        draw.line([(rx, 205), (rx - 15, 255)], fill=(56, 189, 248, 220), width=5)
    finalize(img, "thunderstorm.png")

    # 9. Snow
    img, draw = create_base_canvas(160)
    draw_cloud(draw, 45, 80, 230, 110, color=(148, 163, 184, 240))
    # Snowflakes (asterisks / circles)
    snow_pts = [(90, 225), (140, 255), (180, 220), (225, 250), (130, 215), (205, 210)]
    for sx, sy in snow_pts:
        draw.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=(241, 245, 249, 255))
        draw.line([(sx - 10, sy), (sx + 10, sy)], fill=(241, 245, 249, 255), width=2)
        draw.line([(sx, sy - 10), (sx, sy + 10)], fill=(241, 245, 249, 255), width=2)
    finalize(img, "snow.png")

    # 10. Fog
    img, draw = create_base_canvas(160)
    draw_cloud(draw, 60, 60, 200, 95, color=(148, 163, 184, 180))
    fog_bars = [
        (50, 180, 270, 194),
        (70, 210, 250, 224),
        (40, 240, 280, 254),
    ]
    for x1, y1, x2, y2 in fog_bars:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=7, fill=(203, 213, 225, 220))
    finalize(img, "fog.png")

    # 11. Wind
    img, draw = create_base_canvas(160)
    wind_paths = [
        [(50, 110), (220, 110), (250, 90), (230, 70), (200, 85)],
        [(40, 160), (240, 160), (265, 180), (245, 205), (215, 190)],
        [(70, 210), (200, 210), (225, 230), (210, 250), (185, 240)],
    ]
    for pts in wind_paths:
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=(56, 189, 248, 230), width=8)
    finalize(img, "wind.png")

    # 12. Humidity (Droplet)
    img, draw = create_base_canvas(160)
    # Droplet shape
    tip = (160, 60)
    left = (95, 190)
    bottom = (160, 245)
    right = (225, 190)
    draw.polygon([tip, left, (110, 230), bottom, (210, 230), right], fill=(14, 165, 233, 255))
    draw.ellipse([95, 140, 225, 250], fill=(14, 165, 233, 255))
    # Specular shine
    draw.ellipse([120, 160, 150, 200], fill=(255, 255, 255, 160))
    finalize(img, "humidity.png")

    # 13. Pressure (Gauge / Barometer)
    img, draw = create_base_canvas(160)
    draw.ellipse([70, 70, 250, 250], outline=(148, 163, 184, 220), width=12)
    # Dial markings
    draw.arc([80, 80, 240, 240], start=140, end=400, fill=(0, 240, 255, 255), width=8)
    # Needle
    draw.line([(160, 160), (205, 115)], fill=(239, 68, 68, 255), width=7)
    draw.ellipse([148, 148, 172, 172], fill=(241, 245, 249, 255))
    finalize(img, "pressure.png")

    # 14. UV Index
    img, draw = create_base_canvas(160)
    draw_sun(draw, 160, 160, 52, color=(249, 115, 22, 255), ray_color=(251, 146, 60, 240))
    # Protective shield emblem
    shield = [(140, 140), (180, 140), (180, 175), (160, 195), (140, 175)]
    draw.polygon(shield, fill=(255, 255, 255, 240))
    finalize(img, "uv.png")

    # 15. Sunrise
    img, draw = create_base_canvas(160)
    draw.line([(40, 210), (280, 210)], fill=(148, 163, 184, 220), width=8)
    # Half sun rising
    draw.pieslice([85, 135, 235, 285], start=180, end=360, fill=(255, 193, 7, 255))
    # Up arrow
    draw.polygon([(160, 70), (140, 105), (152, 105), (152, 130), (168, 130), (168, 105), (180, 105)], fill=(16, 185, 129, 255))
    finalize(img, "sunrise.png")

    # 16. Sunset
    img, draw = create_base_canvas(160)
    draw.line([(40, 210), (280, 210)], fill=(148, 163, 184, 220), width=8)
    # Half sun setting
    draw.pieslice([85, 135, 235, 285], start=180, end=360, fill=(249, 115, 22, 255))
    # Down arrow
    draw.polygon([(160, 130), (140, 95), (152, 95), (152, 70), (168, 70), (168, 95), (180, 95)], fill=(239, 68, 68, 255))
    finalize(img, "sunset.png")

    # 17. App Logo
    img, draw = create_base_canvas(160)
    # Modern radar ring + Sun + Cloud
    draw.ellipse([30, 30, 290, 290], outline=(0, 240, 255, 160), width=6)
    draw_sun(draw, 195, 125, 45, color=(255, 193, 7, 255), ray_color=(255, 213, 79, 220))
    draw_cloud(draw, 50, 140, 220, 110, color=(248, 250, 252, 250))
    finalize(img, "app_logo.png")

    print(f"Successfully generated weather icons in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all_icons()
