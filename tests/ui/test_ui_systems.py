"""
Test UI/UX improvements for VPB Editor.

Tests the new theme, icon, font, and spacing systems.
"""

import unittest
from vpb.ui.theme import ThemeManager, get_theme_manager, ThemeColors
from vpb.ui.icons import IconManager, get_icon_manager, UIIcons
from vpb.ui.fonts import FontManager, get_font_manager, FontSystem
from vpb.ui.spacing import SpacingManager, get_spacing_manager, SpacingSystem


class TestThemeSystem(unittest.TestCase):
    """Tests for the Theme System."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.theme = ThemeManager()
    
    def test_theme_initialization(self):
        """Test theme manager initialization."""
        self.assertEqual(self.theme.theme_name, "light")
        self.assertIsNotNone(self.theme._colors)
    
    def test_get_color(self):
        """Test getting colors from theme."""
        primary = self.theme.get_color("primary")
        self.assertEqual(primary, ThemeColors.PRIMARY)
        
        bg = self.theme.get_color("bg_primary")
        self.assertEqual(bg, ThemeColors.BG_PRIMARY)
    
    def test_get_color_default(self):
        """Test getting color with default fallback."""
        color = self.theme.get_color("nonexistent", "#FF0000")
        self.assertEqual(color, "#FF0000")
    
    def test_get_rgb(self):
        """Test getting RGB values."""
        rgb = self.theme.get_rgb("primary")
        self.assertIsNotNone(rgb)
        self.assertEqual(len(rgb), 3)
        self.assertTrue(all(0 <= c <= 255 for c in rgb))
    
    def test_theme_switching(self):
        """Test theme switching."""
        self.theme.switch_theme("light")
        self.assertEqual(self.theme.theme_name, "light")
    
    def test_observer_pattern(self):
        """Test observer pattern for theme changes."""
        called = []
        
        def callback(theme_name):
            called.append(theme_name)
        
        self.theme.subscribe(callback)
        self.theme.switch_theme("light")
        
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0], "light")
    
    def test_global_theme_manager(self):
        """Test global theme manager singleton."""
        theme1 = get_theme_manager()
        theme2 = get_theme_manager()
        self.assertIs(theme1, theme2)


class TestIconSystem(unittest.TestCase):
    """Tests for the Icon System."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.icons = IconManager()
    
    def test_icon_initialization(self):
        """Test icon manager initialization."""
        self.assertIsNotNone(self.icons._icons)
        self.assertTrue(len(self.icons._icons) > 0)
    
    def test_get_icon(self):
        """Test getting icons."""
        save_icon = self.icons.get("save")
        self.assertEqual(save_icon, UIIcons.SAVE)
        
        new_icon = self.icons.get("new")
        self.assertEqual(new_icon, UIIcons.NEW)
    
    def test_get_icon_default(self):
        """Test getting icon with default fallback."""
        icon = self.icons.get("nonexistent", "●")
        self.assertEqual(icon, "●")
    
    def test_custom_icon(self):
        """Test setting custom icons."""
        self.icons.set_custom("test", "🎯")
        icon = self.icons.get("test")
        self.assertEqual(icon, "🎯")
        
        self.icons.reset_custom("test")
        icon = self.icons.get("test", "•")
        self.assertEqual(icon, "•")
    
    def test_global_icon_manager(self):
        """Test global icon manager singleton."""
        icons1 = get_icon_manager()
        icons2 = get_icon_manager()
        self.assertIs(icons1, icons2)


class TestFontSystem(unittest.TestCase):
    """Tests for the Font System."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fonts = FontManager()
    
    def test_font_initialization(self):
        """Test font manager initialization."""
        self.assertIsNotNone(self.fonts._fonts)
        self.assertTrue(len(self.fonts._fonts) > 0)
    
    def test_get_font(self):
        """Test getting fonts."""
        heading = self.fonts.get("heading_1")
        self.assertEqual(len(heading), 3)
        family, size, weight = heading
        self.assertIsInstance(family, str)
        self.assertIsInstance(size, int)
        self.assertIsInstance(weight, str)
    
    def test_get_font_components(self):
        """Test getting font components separately."""
        family = self.fonts.get_family("body")
        size = self.fonts.get_size("body")
        weight = self.fonts.get_weight("body")
        
        self.assertIsInstance(family, str)
        self.assertEqual(size, FontSystem.SIZE_BASE)
        self.assertIn(weight, ["normal", "bold"])
    
    def test_scale_font(self):
        """Test scaling font size."""
        scaled = self.fonts.scale_size("body", 1.5)
        family, size, weight = scaled
        
        original_size = FontSystem.SIZE_BASE
        expected_size = int(original_size * 1.5)
        self.assertEqual(size, expected_size)
    
    def test_global_font_manager(self):
        """Test global font manager singleton."""
        fonts1 = get_font_manager()
        fonts2 = get_font_manager()
        self.assertIs(fonts1, fonts2)


class TestSpacingSystem(unittest.TestCase):
    """Tests for the Spacing System."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.spacing = SpacingManager()
    
    def test_spacing_initialization(self):
        """Test spacing manager initialization."""
        self.assertIsNotNone(self.spacing._spacing)
        self.assertIsNotNone(self.spacing._padding)
    
    def test_get_spacing(self):
        """Test getting spacing values."""
        sm = self.spacing.get_spacing("sm")
        self.assertEqual(sm, SpacingSystem.SM)
        
        md = self.spacing.get_spacing("md")
        self.assertEqual(md, SpacingSystem.MD)
    
    def test_get_padding(self):
        """Test getting padding values."""
        normal = self.spacing.get_padding("normal")
        self.assertEqual(len(normal), 2)
        self.assertIsInstance(normal[0], int)
        self.assertIsInstance(normal[1], int)
    
    def test_get_margin(self):
        """Test getting margin values (same as spacing)."""
        margin = self.spacing.get_margin("lg")
        spacing = self.spacing.get_spacing("lg")
        self.assertEqual(margin, spacing)
    
    def test_scale_spacing(self):
        """Test scaling spacing values."""
        scaled = self.spacing.scale_spacing("md", 2.0)
        expected = int(SpacingSystem.MD * 2.0)
        self.assertEqual(scaled, expected)
    
    def test_scale_padding(self):
        """Test scaling padding values."""
        scaled = self.spacing.scale_padding("normal", 1.5)
        self.assertEqual(len(scaled), 2)
        self.assertIsInstance(scaled[0], int)
        self.assertIsInstance(scaled[1], int)
    
    def test_global_spacing_manager(self):
        """Test global spacing manager singleton."""
        spacing1 = get_spacing_manager()
        spacing2 = get_spacing_manager()
        self.assertIs(spacing1, spacing2)


class TestUIIntegration(unittest.TestCase):
    """Integration tests for UI systems."""
    
    def test_all_systems_available(self):
        """Test that all UI systems are available."""
        theme = get_theme_manager()
        icons = get_icon_manager()
        fonts = get_font_manager()
        spacing = get_spacing_manager()
        
        self.assertIsNotNone(theme)
        self.assertIsNotNone(icons)
        self.assertIsNotNone(fonts)
        self.assertIsNotNone(spacing)
    
    def test_theme_colors_valid(self):
        """Test that all theme colors are valid hex strings."""
        theme = get_theme_manager()
        
        color_names = [
            "primary", "success", "warning", "error",
            "bg_primary", "text_primary", "border_light"
        ]
        
        for name in color_names:
            color = theme.get_color(name)
            self.assertTrue(color.startswith("#"))
            self.assertTrue(len(color) in [7, 9])  # #RRGGBB or #RRGGBBAA
    
    def test_icon_availability(self):
        """Test that common icons are available."""
        icons = get_icon_manager()
        
        icon_names = [
            "save", "open", "new", "delete", "copy", "paste",
            "undo", "redo", "zoom_in", "zoom_out", "grid"
        ]
        
        for name in icon_names:
            icon = icons.get(name)
            self.assertIsNotNone(icon)
            self.assertTrue(len(icon) > 0)
    
    def test_font_hierarchy(self):
        """Test that font hierarchy is consistent."""
        fonts = get_font_manager()
        
        h1_size = fonts.get_size("heading_1")
        h2_size = fonts.get_size("heading_2")
        body_size = fonts.get_size("body")
        small_size = fonts.get_size("small")
        
        self.assertGreater(h1_size, h2_size)
        self.assertGreater(h2_size, body_size)
        self.assertGreater(body_size, small_size)
    
    def test_spacing_8pt_grid(self):
        """Test that spacing follows 8pt grid system."""
        spacing = get_spacing_manager()
        
        sm = spacing.get_spacing("sm")
        md = spacing.get_spacing("md")
        lg = spacing.get_spacing("lg")
        
        # All should be multiples of 8 (or 4 for half-steps)
        self.assertEqual(sm % 4, 0)
        self.assertEqual(md % 8, 0)
        self.assertEqual(lg % 8, 0)


if __name__ == "__main__":
    unittest.main()
