# Changelog

## 1.2.0 – 2026-10-20

### Settings window
- Tidier: 7 pages instead of 9. "Cards" and "Studying" are now one page (**Studying & cards**), "Shape" and "Text" are merged, performance moved to "Advanced"
- The preview follows you: switching pages or changing a setting jumps to the view where you can see it (home, study, answer side, windows)
- **Windows preview for every window**: card browser, editor, statistics, deck options, Anki preferences and add-ons window, each in the chosen style (statistics and deck options are Anki's real pages)
- Card designs: the buttons only become active once a style and note types are picked, and a line below says what's missing; click anywhere on a row to tick a note type; unused note types are hidden; a second click on a style removes it from the preview
- Fixed: choosing a card design no longer locks the study background; "Background while studying" now always shows its effect in the preview and applying a card design no longer changes it
- Answer buttons fit into the study preview

### Online gallery
- Much faster: thumbnail grid with small preview images (via wsrv.nl) instead of downloading every full-size wallpaper; the original is only downloaded when you use it
- The image list is cached for a few days, so the gallery opens instantly
- Fixed: Omarchy could disappear from the source list after picking ML4W (now two always-visible buttons); a slow answer can no longer show the wrong source or image

### Add-on center
- Pin add-ons to the top with the pin button

## 1.1.0 – 2026-10-20

### Designs & wallpapers
- New **Designs** page: built-in theme packs (illustrations, photos, Omarchy color themes, patterns) and, kept separate, **My designs**: save your current look, turn any wallpaper into a complete design (accent and background tones adapt), export/import as `.deckorator` files
- **46 theme packs** for a complete look in one click
- **12 illustrated wallpapers** drawn for Deckorator, tinted with your accent color, with light and dark versions: Fuji, lofi city, sakura, mountains, planet, flow lines, topography, Bauhaus, dunes, aurora, clouds, seigaiha
- **12 photo wallpapers** (CC0/public domain from Wikimedia Commons), including light/dark pairs that switch with Anki's mode (Winter, By the Water, Beach)
- **23 Omarchy color themes** (Catppuccin, Gruvbox, Nord, Tokyo Night, Kanagawa …)
- **Online gallery**: browse Omarchy and ML4W wallpapers on GitHub and use them as a design (Omarchy images get the colors of their theme). Images are loaded on demand and not bundled
- Separate background image for dark mode
- **Banner** in the top bar (illustration, photo or own image, three heights), either across the whole bar or only inside the tab capsule; the bar stays calm while studying

### Colors
- 21 color presets plus a 24-color quick pick next to the color picker
- Fixed: color presets did nothing while the accent came from the system or wallpaper

### Card designs
- Six styles for any note type: Clean, Index card, Minimal, Focus, Study notes, Like my theme
- Live preview on your own cards; stored in the note type (works on mobile after syncing) and fully reversible

### Windows
- Card browser, editor (add, edit, browse), statistics, deck options, Anki preferences and add-ons window in the Deckorator look
- **Bold** style (spotlight, floating glass panels, accent headers) or **Subtle** (colors and corners only)
- New **Areas** page: bold, subtle or Anki's original look for every part of Anki separately, plus "Everything to Anki original"
- **Windows** preview tab showing the card browser and preferences in the chosen style
- Flag, marked, suspended and selection colors in the browser stay exactly as in Anki

### Add-ons
- **Add-on center**: your add-ons as cards with a switch, settings and page link; Anki's own buttons keep working
- Content that other add-ons place below the deck list automatically gets a matching glass card
- **Conflict check**: detects other theme add-ons and offers to adjust areas or disable them

### Other
- Glow effects around buttons, tiles and the top bar can be switched off
- Fixed: the color buttons' stylesheet could not be parsed

## 1.0.0 – 2026-10-20

First release on AnkiWeb (`1326296861`).
- Theme for the deck list, overview and study screen with presets, accent color from the system or wallpaper, pattern and wallpaper backgrounds
- Calm study mode, readable review counters, "studied today" highlight
- Review Heatmap support: fully restyled, colors only, or left untouched
- Automatic performance mode for weak hardware
- Settings window with a live preview of your own decks and cards
