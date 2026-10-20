# Einstellungsfenster mit Live-Vorschau. Änderungen werden erst mit
# "Übernehmen"/"Speichern" gespeichert und auf Ankis Hauptfenster angewendet.
import json
import os
import shutil

from anki.lang import current_lang
from aqt import mw
from aqt.qt import *
from aqt.theme import theme_manager
from aqt.utils import askUser, getFile, getSaveFile, showWarning, tooltip

from . import desktop, theme, ui
from .preview import ThemePreview
from .ui import ColorButton, Section, Toggle

ADDON_DIR = os.path.dirname(__file__)
USER_DIR = os.path.join(ADDON_DIR, "user_files")

STRINGS = {
    "title": ("Deckorator – Theme-Einstellungen", "Deckorator – Theme settings"),
    "page_look": ("Aussehen", "Appearance"), "page_shape": ("Form", "Shape"),
    "page_text": ("Schrift", "Text"), "page_study": ("Lernen", "Studying"),
    "page_addons": ("Add-ons", "Add-ons"), "page_advanced": ("Erweitert", "Advanced"),
    "page_areas": ("Bereiche", "Areas"), "page_designs": ("Designs", "Designs"), "page_cards": ("Karten", "Cards"),
    "card_styles": ("Karten-Designs", "Card designs"),
    "card_styles_hint": ("Fertige Stile für deine Karten, wie bei der Muskeltabelle, für beliebige Decks. Klick auf einen "
                         "Stil zeigt ihn in der Vorschau an einer deiner Karten. Die Farben kommen aus deinem Theme.",
                         "Ready-made styles for your cards, like the muscle table, for any deck. Clicking a style shows "
                         "it in the preview on one of your cards. Colors come from your theme."),
    "card_style_names": ({"clean": "Klar", "index": "Karteikarte", "minimal": "Minimal",
                          "focus": "Fokus", "notes": "Lernzettel", "theme": "Wie mein Theme"},
                         {"clean": "Clean", "index": "Index card", "minimal": "Minimal",
                          "focus": "Focus", "notes": "Study notes", "theme": "Like my theme"}),
    "card_target": ("Für welche Karten?", "Which cards?"),
    "card_target_hint": ("Der Stil wird im Notiztyp gespeichert und gilt für alle Karten dieses Typs, auch auf dem Handy "
                         "nach dem Synchronisieren. Dein eigenes CSS bleibt erhalten; „Stil entfernen“ stellt das Original wieder her.",
                         "The style is stored in the note type and applies to all its cards, also on your phone after "
                         "syncing. Your own CSS stays; “Remove style” restores the original."),
    "card_by_deck": ("Aus Stapel", "From deck"), "card_pick_deck": ("Notiztypen eines Stapels auswählen…", "Select note types of a deck…"),
    "card_type_row": ("{name} ({count} Karten)", "{name} ({count} cards)"),
    "card_apply": ("Auf ausgewählte anwenden", "Apply to selected"), "card_remove": ("Stil entfernen", "Remove style"),
    "card_need_choice": ("Wähle einen Stil und mindestens einen Notiztyp.", "Pick a style and at least one note type."),
    "card_need_types": ("Wähle mindestens einen Notiztyp.", "Pick at least one note type."),
    "card_confirm": ("Den Stil auf {n} Notiztyp(en) anwenden? Das ändert deren CSS (umkehrbar mit „Stil entfernen“).",
                     "Apply the style to {n} note type(s)? This changes their CSS (reversible with “Remove style”)."),
    "card_applied": ("Kartenstil angewendet", "Card style applied"), "card_removed": ("Kartenstil entfernt", "Card style removed"),
    "packs_art": ("Illustrationen", "Illustrations"), "packs_photo": ("Fotos", "Photos"),
    "packs_pattern": ("Minimal & Muster", "Minimal & patterns"),
    "packs_omarchy": ("Omarchy-Farbthemen", "Omarchy color themes"),
    "packs_omarchy_hint": ("Die Farbpaletten der Omarchy-Themes (Catppuccin, Gruvbox, Nord, Tokyo Night …) als Deckorator-Looks. "
                           "Die passenden Wallpaper findest du in der Online-Galerie oben.",
                           "The color palettes of the Omarchy themes (Catppuccin, Gruvbox, Nord, Tokyo Night …) as Deckorator "
                           "looks. Matching wallpapers are in the online gallery above."),
    "my_designs": ("Meine Designs", "My designs"),
    "my_designs_hint": ("Deine eigenen Looks, getrennt von den eingebauten Paketen. „Design aus Bild“ macht aus einem "
                        "Wallpaper einen kompletten Look: Akzentfarbe, Hintergrundtöne und Bild passen sich an. "
                        "Rechtsklick auf ein Design zum Exportieren oder Löschen.",
                        "Your own looks, separate from the built-in packs. “Design from image” turns a wallpaper into "
                        "a complete look: accent color, background tones and image adapt. Right-click a design to "
                        "export or delete it."),
    "save_design": ("Aktuellen Look speichern…", "Save current look…"),
    "gallery_open": ("Online-Galerie…", "Online gallery…"), "gallery": ("Online-Galerie", "Online gallery"),
    "gallery_note": ("Wallpaper aus öffentlichen Sammlungen auf GitHub (Omarchy, ML4W). Liste und Bilder werden erst jetzt "
                     "direkt von GitHub geladen. Die Bilder gehören ihren Urhebern und sind für deinen eigenen Gebrauch; "
                     "teile Designs mit diesen Bildern nicht weiter.",
                     "Wallpapers from public collections on GitHub (Omarchy, ML4W). The list and images are loaded "
                     "directly from GitHub only now. The images belong to their creators and are for your own use; "
                     "don't share designs containing them."),
    "gallery_repo": ("Auf GitHub ansehen", "View on GitHub"), "gallery_filter": ("Suchen…", "Search…"),
    "gallery_pick": ("Wähle links ein Bild für die Vorschau.", "Pick an image on the left to preview it."),
    "gallery_loading": ("Wird geladen…", "Loading…"), "gallery_error": ("Konnte nicht laden: {err}", "Couldn't load: {err}"),
    "gallery_use": ("Als Design übernehmen", "Use as design"),
    "design_from_image": ("Design aus Bild…", "Design from image…"),
    "import_design": ("Importieren…", "Import…"), "export_design": ("Exportieren…", "Export…"),
    "apply_design": ("Anwenden", "Apply"), "delete_design": ("Löschen", "Delete"),
    "design_name": ("Name des Designs:", "Design name:"), "my_design_default": ("Mein Design", "My design"),
    "design_saved": ("Design gespeichert", "Design saved"), "design_exported": ("Design exportiert", "Design exported"),
    "design_tip": ("Klick: anwenden · Rechtsklick: exportieren oder löschen", "Click: apply · Right-click: export or delete"),
    "no_designs": ("Noch keine eigenen Designs. Speichere deinen aktuellen Look oder erstelle eins aus einem Wallpaper.",
                   "No designs yet. Save your current look or create one from a wallpaper."),
    "gallery_hint": ('Schöne Wallpaper findest du z.B. in den <a href="https://github.com/basecamp/omarchy/tree/master/themes">'
                     'Omarchy-Themes</a> (Ordner „backgrounds“). Achte beim Weitergeben eigener Designs auf die Lizenz der Bilder.',
                     'Great wallpapers can be found e.g. in the <a href="https://github.com/basecamp/omarchy/tree/master/themes">'
                     'Omarchy themes</a> ("backgrounds" folders). Mind the image license when sharing your designs.'),
    "bg_image_dark": ("Bild für Dunkel", "Image for dark mode"),
    "bg_image_dark_hint": ("Optional: eigenes Bild nur für den Dunkelmodus.", "Optional: separate image for dark mode."),
    "banner_area": ("Bereich", "Area"), "ba_bar": ("Ganze Leiste", "Whole bar"), "ba_capsule": ("Nur die Kapsel mit den Reitern", "Only the tab capsule"),
    "areas_hint": ("Für jeden Teil von Anki einzeln: Deckorator-Look oder Anki-Original. Bei Fenstern zusätzlich "
                   "„Kräftig“ (Spotlight, Glaskarten, Akzente) oder „Dezent“ (nur Farben und Rundungen).",
                   "For every part of Anki separately: Deckorator look or Anki's original. Windows can also be "
                   "“Bold” (spotlight, glass cards, accents) or “Subtle” (colors and corners only)."),
    "areas_home": ("Startseite & Hauptfenster", "Home & main window"),
    "areas_windows": ("Fenster", "Windows"),
    "mode_on": ("Deckorator", "Deckorator"), "mode_original": ("Anki-Original", "Anki original"),
    "mode_bold": ("Kräftig", "Bold"), "mode_subtle": ("Dezent", "Subtle"), "mode_colors": ("Nur Farben", "Colors only"),
    "all_original": ("Alles auf Anki-Original", "Everything to Anki original"),
    "all_bold": ("Alles auf Kräftig", "Everything to bold"),
    "style_art": ("Illustration", "Illustration"),
    "art_motif": ("Motiv", "Motif"),
    "art_names": ({"fuji": "Fuji", "lofi_city": "Lofi-Stadt", "sakura": "Sakura", "mountains": "Gebirge",
                   "planet": "Planet", "flow": "Linienfluss", "topo": "Topografie", "bauhaus": "Bauhaus",
                   "dunes": "Dünen", "aurora": "Polarlicht", "clouds": "Wolken", "seigaiha": "Seigaiha"},
                  {"fuji": "Fuji", "lofi_city": "Lofi City", "sakura": "Sakura", "mountains": "Mountains",
                   "planet": "Planet", "flow": "Flow Lines", "topo": "Topography", "bauhaus": "Bauhaus",
                   "dunes": "Dunes", "aurora": "Aurora", "clouds": "Clouds", "seigaiha": "Seigaiha"}),
    "banner": ("Banner in der oberen Leiste", "Banner in the top bar"),
    "banner_hint": ("Ein Motiv hinter Stapel, Hinzufügen, Kartenverwaltung … Beim Lernen bleibt die Leiste ruhig.",
                    "A motif behind Decks, Add, Browse … The bar stays calm while you study."),
    "banner_motif": ("Motiv", "Motif"), "banner_none": ("Kein Banner", "No banner"),
    "banner_art": ("Illustration: {name}", "Illustration: {name}"), "banner_photo": ("Foto: {name}", "Photo: {name}"),
    "banner_image": ("Eigenes Bild", "Own image"), "banner_height": ("Höhe", "Height"),
    "bh_small": ("Schmal", "Slim"), "bh_medium": ("Mittel", "Medium"), "bh_large": ("Hoch", "Tall"),
    "presets": ("Farbvorlagen", "Color presets"),
    "packs": ("Theme-Pakete", "Theme packs"),
    "packs_hint": ("Ein kompletter Look auf einen Klick: Hintergrundbild, Farben, Formen und Fensterstil.",
                   "A complete look in one click: wallpaper, colors, shapes and window style."),
    "pack_names": ({"fuji": "Fuji", "lofi": "Lofi-Nacht", "sakura": "Sakura", "mountains": "Gebirge",
                    "planet": "Planet", "flow": "Linienfluss", "topo": "Topografie", "bauhaus": "Bauhaus",
                    "dunes": "Dünen", "aurora": "Polarlicht", "clouds": "Wolken", "seigaiha": "Seigaiha",
                    "winter": "Winter (Hell/Dunkel)", "water": "Am Wasser (Hell/Dunkel)", "beach": "Strand (Hell/Dunkel)",
                    "sea": "Stille See", "dune": "Düne", "forest": "Nebelwald", "sunset": "Abendrot",
                    "stars": "Sternennacht", "lake": "Bergsee", "minimal": "Minimal", "paper": "Papier"},
                   {"fuji": "Fuji", "lofi": "Lofi Night", "sakura": "Sakura", "mountains": "Mountains",
                    "planet": "Planet", "flow": "Flow Lines", "topo": "Topography", "bauhaus": "Bauhaus",
                    "dunes": "Dunes", "aurora": "Aurora", "clouds": "Clouds", "seigaiha": "Seigaiha",
                    "winter": "Winter (light/dark)", "water": "By the Water (light/dark)", "beach": "Beach (light/dark)",
                    "sea": "Calm Sea", "dune": "Dune", "forest": "Misty Forest", "sunset": "Afterglow",
                    "stars": "Starry Night", "lake": "Mountain Lake", "minimal": "Minimal", "paper": "Paper"}), "colors": ("Farben", "Colors"), "background": ("Hintergrund", "Background"),
    "accent": ("Akzentfarbe", "Accent color"),
    "bg_light": ("Hell", "Light"), "bg_dark": ("Dunkel", "Dark"),
    "bg_style": ("Stil", "Style"), "bg_intensity": ("Intensität", "Intensity"),
    "bg_image": ("Bild", "Image"), "choose": ("Auswählen…", "Choose…"),
    "remove": ("Entfernen", "Remove"), "none": ("Keins", "None"),
    "style_solid": ("Einfarbig", "Solid"), "style_spotlight": ("Spotlight: Licht von oben", "Spotlight: light from above"),
    "style_dots": ("Punktraster", "Dot grid"), "style_grid": ("Linienraster", "Line grid"),
    "style_grain": ("Körnung", "Grain"), "style_waves": ("Wellen", "Waves"), "style_image": ("Eigenes Bild", "Custom image"),
    "style_desktop": ("Desktop-Hintergrund (folgt deinem Wallpaper)", "Desktop wallpaper (follows yours)"),
    "desktop_hint": ("Aktuell: {name}. Wird bei jedem Start von Anki neu abgeglichen. Live- und Video-Wallpaper "
                     "erscheinen als Standbild.",
                     "Currently: {name}. Re-synced every time Anki starts. Live and video wallpapers "
                     "show up as a still image."),
    "windows": ("Andere Fenster", "Other windows"),
    "windows_hint": ("Kartenverwaltung, Hinzufügen, Statistik, Stapeloptionen, Anki-Einstellungen und Add-on-Liste.",
                     "Card browser, add, statistics, deck options, Anki preferences and add-ons window."),
    "window_style": ("Stil", "Style"),
    "ws_bold": ("Kräftig: Spotlight, Glaskarten, Akzente", "Bold: spotlight, glass cards, accents"),
    "ws_subtle": ("Dezent: nur Farben und Rundungen", "Subtle: colors and corners only"),
    "performance": ("Leistung", "Performance"), "perf_mode": ("Effekte", "Effects"),
    "perf_auto": ("Automatisch an die Hardware anpassen", "Adapt to the hardware automatically"),
    "perf_full": ("Alle Effekte", "All effects"),
    "perf_light": ("Sparsam: ohne Unschärfe, leichte Schatten", "Light: no blur, softer shadows"),
    "hw_detected": ("Erkannt: {facts}. {verdict}", "Detected: {facts}. {verdict}"),
    "hw_threads": ("{n} CPU-Threads", "{n} CPU threads"), "hw_ram": ("{n} GB RAM", "{n} GB RAM"),
    "hw_battery": ("läuft auf Akku", "running on battery"), "hw_software": ("Software-Rendering", "software rendering"),
    "hw_weak": ("Automatisch wird der sparsame Modus genutzt.", "Automatic mode uses the light setting."),
    "hw_strong": ("Automatisch bleiben alle Effekte an.", "Automatic mode keeps all effects on."),
    "no_wallpaper": ("Der Desktop-Hintergrund wurde nicht gefunden.", "Couldn't find the desktop wallpaper."),
    "accent_source": ("Quelle", "Source"),
    "src_manual": ("Selbst wählen", "Pick myself"), "src_system": ("Akzentfarbe des Systems", "System accent color"),
    "src_wallpaper": ("Aus dem Desktop-Hintergrund", "From the desktop wallpaper"),
    "src_hint": ("Wird bei jedem Start von Anki neu gelesen. Ändert sich dein Hintergrund, zieht die Farbe mit.",
                 "Re-read every time Anki starts. If your wallpaper changes, the color follows."),
    "src_found": ("Erkannt: {color} ({where})", "Detected: {color} ({where})"),
    "src_failed": ("Nichts gefunden, die bisherige Farbe bleibt.", "Nothing found, keeping the current color."),
    "src_system_where": ("System", "system"),
    "redetect": ("Erneut erkennen", "Detect again"),
    "glass_title": ("Glas", "Glass"),
    "glass_hint": ("Die Unschärfe sieht man nur, wenn hinter den Flächen ein Muster oder Bild liegt, "
                   "z.B. bei Punktraster, Wellen oder Desktop-Hintergrund.",
                   "Blur is only visible when a pattern or image sits behind the panels, "
                   "e.g. with dot grid, waves or desktop wallpaper."),
    "glass": ("Durchscheinende Flächen mit Unschärfe", "Translucent panels with blur"),
    "blur": ("Unschärfe", "Blur"), "opacity": ("Deckkraft", "Opacity"),
    "shapes": ("Formen", "Shapes"),
    "radius": ("Eckenradius", "Corner radius"), "buttons": ("Buttons", "Buttons"),
    "btn_pill": ("Pille", "Pill"), "btn_rounded": ("Abgerundet", "Rounded"), "btn_square": ("Eckig", "Square"),
    "shadow": ("Schatten", "Shadows"), "shadow_levels": (("Aus", "Leicht", "Mittel", "Stark"), ("Off", "Light", "Medium", "Strong")),
    "bars": ("Leisten", "Bars"),
    "toolbar": ("Obere Leiste", "Top bar"), "tb_floating": ("Schwebende Kapsel", "Floating capsule"),
    "tb_flat": ("Flach", "Flat"), "compact": ("Kompakte Abstände", "Compact spacing"),
    "font": ("Schriftart", "Font"), "font_default": ("Anki-Standardschrift verwenden", "Use Anki's default font"),
    "font_scale": ("Größe", "Size"),
    "font_hint": ("Gilt für Deckliste, Übersicht und Leisten. Karten behalten die Schrift ihres Notiztyps.",
                  "Applies to the deck list, overview and bars. Cards keep their note type's font."),
    "display": ("Anzeige", "Display"),
    "badges": ("Zähler als farbige Badges", "Counts as colored badges"),
    "highlight_today": ("„Heute gelernt“ auf der Startseite hervorheben", "Highlight “studied today” on the home screen"),
    "help": ("Hilfe & Feedback", "Help & feedback"),
    "help_hint": ("Kopiert einen Bericht über Anki-Version, System, erkannte Hardware und die letzten Fehler. "
                  "Nichts wird automatisch gesendet; du entscheidest, wo du ihn einfügst.",
                  "Copies a report with Anki version, system, detected hardware and recent errors. "
                  "Nothing is sent automatically; you decide where to paste it."),
    "copy_diag": ("Diagnosebericht kopieren", "Copy diagnostic report"),
    "diag_copied": ("Bericht in die Zwischenablage kopiert", "Report copied to the clipboard"),
    "answers": ("Antwort-Buttons nach Bewertung einfärben", "Tint answer buttons by rating"),
    "animations": ("Animationen", "Animations"),
    "motion": ("Bewegung", "Motion"),
    "motion_hint": ("Wenn in Anki „Bewegung reduzieren“ an ist, bleiben Animationen ohnehin aus.",
                    "If Anki's “Reduce motion” is on, animations stay off anyway."),
    "areas": ("Anwenden auf", "Apply to"),
    "area_main": ("Deckliste, Übersicht und Leisten", "Deck list, overview and bars"),
    "area_review_bar": ("Untere Leiste beim Lernen", "Bottom bar while studying"),
    "area_browser": ("Kartenverwaltung (Browse)", "Card browser"),
    "area_addons": ("Add-on-Liste", "Add-ons window"),
    "area_preferences": ("Anki-Einstellungen", "Anki preferences"),
    "area_editor": ("Editor (Hinzufügen, Bearbeiten, Kartenverwaltung)", "Editor (add, edit, card browser)"),
    "area_stats": ("Statistik", "Statistics"),
    "area_deck_options": ("Stapeloptionen", "Deck options"),
    "area_other": ("Andere Fenster (Kartenvorschau, Notiztypen …)", "Other windows (card preview, note types …)"),
    "review_bg": ("Hintergrund beim Lernen", "Background while studying"),
    "rb_calm": ("Ruhig: Theme-Farbe, keine Effekte", "Calm: theme color, no effects"),
    "rb_full": ("Wie auf der Startseite", "Same as the home screen"),
    "rb_note": ("Vom Notiztyp (Theme hält sich raus)", "From the note type (theme stays out)"),
    "rb_hint": ("Beim Lernen steht die Karte im Mittelpunkt. „Ruhig“ übernimmt die Farbe deines Themes, "
                "verzichtet aber auf Farbflecken und Bild, damit nichts ablenkt.",
                "While studying, the card comes first. “Calm” keeps your theme's color but drops "
                "blobs and images so nothing distracts you."),
    "heatmap": ("Review Heatmap", "Review Heatmap"),
    "hm_theme": ("Komplett anpassen: Karte, runde Zellen, Akzentfarbe", "Fully restyle: card, rounded cells, accent color"),
    "hm_colors": ("Nur Farben anpassen, Form bleibt original", "Colors only, keep the original shape"),
    "hm_original": ("Nicht verändern (Original)", "Leave untouched (original)"),
    "hm_hint": ("Du entscheidest, ob Deckorator die Heatmap umgestaltet. „Nicht verändern“ lässt sie exakt so, "
                "wie das Heatmap-Add-on sie zeichnet.",
                "You decide whether Deckorator restyles the heatmap. “Leave untouched” keeps it exactly "
                "as the heatmap add-on draws it."),
    "hm_missing": ("Review Heatmap ist nicht installiert oder deaktiviert. Die Einstellung greift, sobald es aktiv ist.",
                   "Review Heatmap is not installed or disabled. The setting applies once it's active."),
    "hm_style": ("Darstellung", "Style"),
    "addon_center": ("Add-on-Zentrale", "Add-on center"),
    "embed_title": ("Inhalte anderer Add-ons", "Content from other add-ons"),
    "embed_hint": ("Was andere Add-ons unter die Deckliste setzen (z.B. Statistiken, Fortschrittsbalken), bekommt "
                   "automatisch eine passende Glaskarte, ohne dass Deckorator das Add-on kennen muss.",
                   "Whatever other add-ons place below the deck list (e.g. stats, progress bars) automatically gets "
                   "a matching glass card, without Deckorator having to know the add-on."),
    "embed_on": ("Automatisch einbetten", "Embed automatically"),
    "conflicts_title": ("Konflikt-Check", "Conflict check"),
    "conflicts_none": ("Keine anderen Theme-Add-ons gefunden.", "No other theme add-ons found."),
    "conflicts_found": ("Diese Add-ons ändern ebenfalls Ankis Aussehen und können sich mit Deckorator überlagern:\n{names}\n"
                        "Tipp: Stell überlappende Bereiche unter „Bereiche“ auf „Anki-Original“.",
                        "These add-ons also change Anki's look and may clash with Deckorator:\n{names}\n"
                        "Tip: set overlapping areas to “Anki original” under “Areas”."),
    "conflict_text": ("Deckorator hat Add-ons gefunden, die ebenfalls Ankis Aussehen ändern:\n\n{names}\n\n"
                      "Zwei Themes gleichzeitig können sich überlagern und kaputt aussehen. Du kannst die "
                      "überlappenden Bereiche in Deckorator auf „Anki-Original“ stellen oder das andere Add-on deaktivieren.",
                      "Deckorator found add-ons that also change Anki's look:\n\n{names}\n\n"
                      "Two themes at once can overlap and look broken. You can set overlapping areas in Deckorator "
                      "to “Anki original” or disable the other add-on."),
    "conflict_areas": ("Bereiche anpassen", "Adjust areas"), "conflict_disable": ("Andere deaktivieren", "Disable others"),
    "conflict_ignore": ("Beides behalten", "Keep both"),
    "conflict_restart": ("Deaktiviert. Die Änderung wirkt nach einem Neustart von Anki.", "Disabled. Takes effect after restarting Anki."),
    "addon_center_hint": ("Zeigt deine Add-ons als Karten mit Schalter, Einstellungen und Link zur Seite, statt als graue "
                          "Namensliste. Alle Knöpfe von Anki (Löschen, Updates suchen …) funktionieren weiter.",
                          "Shows your add-ons as cards with a switch, settings and a link to their page instead of a "
                          "grey list of names. All of Anki's buttons (delete, check for updates …) keep working."),
    "addon_center_on": ("Karten statt Liste", "Cards instead of a list"),
    "ac_updated": ("aktualisiert {date}", "updated {date}"), "ac_incompatible": ("nicht kompatibel", "not compatible"),
    "ac_settings": ("Einstellungen", "Settings"), "ac_page": ("Seite", "Page"),
    "ac_toggle": ("An/Aus (wirkt nach Neustart)", "On/off (applies after restart)"),
    "custom_css": ("Eigenes CSS", "Custom CSS"),
    "custom_css_hint": ("Wird zuletzt angehängt und überschreibt damit alles andere.",
                        "Appended last, so it overrides everything else."),
    "share": ("Teilen", "Share"),
    "share_hint": ("Speichert alle Einstellungen außer dem Hintergrundbild als JSON-Datei.",
                   "Saves all settings except the background image as a JSON file."),
    "export": ("Exportieren…", "Export…"), "import": ("Importieren…", "Import…"),
    "reset": ("Auf Standard zurücksetzen", "Reset to defaults"),
    "cancel": ("Abbrechen", "Cancel"), "apply": ("Übernehmen", "Apply"), "save": ("Speichern", "Save"),
    "light": ("Hell", "Light"), "dark": ("Dunkel", "Dark"),
    "view_home": ("Startseite", "Home"), "view_study": ("Lernen", "Study"), "view_windows": ("Fenster", "Windows"),
    "mock_info": ("Kartenverwaltung: {browser} · Anki-Einstellungen: {prefs}", "Card browser: {browser} · Preferences: {prefs}"),
    "mock_search": ("Karten suchen…", "Search cards…"),
    "mock_columns": (("Sortierfeld", "Fällig", "Stapel"), ("Sort field", "Due", "Deck")),
    "mock_rows": ((("M. biceps brachii", "Morgen", "Anatomie"), ("Ursprung M. deltoideus", "Heute", "Anatomie"),
                   ("Nernst-Gleichung", "In 3 Tagen", "Physiologie"), ("la biblioteca", "Neu", "Spanisch"),
                   ("Hauptstadt von Japan", "Neu", "Hauptstädte"), ("Wirkmechanismus ASS", "Heute", "Pharmakologie")),
                  (("Biceps brachii", "Tomorrow", "Anatomy"), ("Origin of deltoid", "Today", "Anatomy"),
                   ("Nernst equation", "In 3 days", "Physiology"), ("la biblioteca", "New", "Spanish"),
                   ("Capital of Japan", "New", "Capitals"), ("Aspirin mechanism", "Today", "Pharmacology"))),
    "mock_sidebar": ((("Heute", ("Fällig", "Hinzugefügt")), ("Flaggen", ("Rot", "Blau")), ("Stapel", ("Anatomie", "Physiologie"))),
                     (("Today", ("Due", "Added")), ("Flags", ("Red", "Blue")), ("Decks", ("Anatomy", "Physiology")))),
    "mock_group": ("Allgemein", "General"),
    "mock_checks": (("Nach Updates suchen", "Animationen deaktivieren", "Restliche Karten anzeigen"),
                    ("Check for updates", "Disable animations", "Show remaining card count")),
    "mock_spin": ("Neue Karten pro Tag", "New cards per day"),
    "mock_tabs": (("Erscheinungsbild", "Wiederholung", "Bearbeiten"), ("Appearance", "Review", "Editing")),
    "other_card": ("Andere Karte", "Another card"), "image_card": ("Karte mit Bild", "Card with image"),
    "answer_side": ("Antwort zeigen", "Show answer"),
    "no_image": ("In deiner Sammlung gibt es keine Karte mit Bild.", "Your collection has no card with an image."),
    "no_cards": ("Beispielkarte, deine Sammlung ist noch leer", "Sample card, your collection is empty"),
    "no_decks": ("Öffne einmal die Stapelübersicht, dann erscheinen hier deine Stapel.",
                 "Open the deck list once and your decks will show up here."),
    "demo_q": ("Wie heißt die Hauptstadt von Österreich?", "What is the capital of Austria?"),
    "demo_a": ("Wien", "Vienna"),
    "saved": ("Theme gespeichert", "Theme saved"), "import_err": ("Datei konnte nicht gelesen werden:", "Could not read file:"),
    "quick_colors": ("Schnellwahl", "Quick pick"),
    "glow": ("Leuchteffekte (farbiger Schein um Buttons, Kacheln und obere Leiste)", "Glow effects (colored halo around buttons, tiles and top bar)"),
    "preset_names": ({"rose": "Rosé", "crimson": "Karmin", "tangerine": "Mandarine", "gold": "Gold", "lime": "Limette",
                      "emerald": "Smaragd", "cyan": "Cyan", "indigo": "Indigo", "violet": "Violett", "fuchsia": "Fuchsia",
                      "pink": "Pink", "mint": "Minze", "slate": "Schiefer", "ocean": "Ozean", "forest": "Wald", "lavender": "Lavendel", "amber": "Bernstein",
                      "coral": "Koralle", "teal": "Petrol", "graphite": "Graphit"},
                     {"rose": "Rosé", "crimson": "Crimson", "tangerine": "Tangerine", "gold": "Gold", "lime": "Lime",
                      "emerald": "Emerald", "cyan": "Cyan", "indigo": "Indigo", "violet": "Violet", "fuchsia": "Fuchsia",
                      "pink": "Pink", "mint": "Mint", "slate": "Slate", "ocean": "Ocean", "forest": "Forest", "lavender": "Lavender", "amber": "Amber",
                      "coral": "Coral", "teal": "Teal", "graphite": "Graphite"}),
}

PAGES = ("designs", "look", "cards", "shape", "text", "study", "areas", "addons", "advanced")
# Werte, die an diesen Rechner gebunden sind und beim Teilen nicht mitwandern
PRIVATE_KEYS = ("bg_image", "bg_image_dark", "banner_image", "desktop_image", "desktop_sig", "design", "conflicts_ack")


def t(key):
    de, en = STRINGS[key]
    return de if current_lang.startswith("de") else en


HEATMAP_ID = "1771074083"  # Review Heatmap auf AnkiWeb


def diagnostics(api, cfg):
    """Text für Fehlerberichte. Keine Pfade außer Dateinamen, keine Karteninhalte."""
    import platform

    from anki.buildinfo import version as anki_version
    from aqt.qt import QT_VERSION_STR
    from . import log

    try:
        from PyQt6.QtWebEngineCore import qWebEngineChromiumVersion
        chromium = qWebEngineChromiumVersion()
    except Exception:
        chromium = "?"
    hw = api.hardware()
    wall = desktop.wallpaper_path(theme_manager.night_mode)
    lines = [
        f"Deckorator {api.VERSION} | Anki {anki_version} | Qt {QT_VERSION_STR} | Chromium {chromium}",
        f"OS: {platform.platform()} | Desktop: {os.environ.get('XDG_CURRENT_DESKTOP', '-')} "
        f"| Session: {os.environ.get('XDG_SESSION_TYPE', '-')} | Night mode: {theme_manager.night_mode}",
        f"Hardware: {hw['threads']} threads, {hw['ram'] and round(hw['ram'])} GB RAM, battery={hw['battery']}, "
        f"software={hw['software']} -> weak={hw['weak']} | performance={cfg['performance']} "
        f"-> light={api.effective(cfg)['_light']}",
        f"Desktop: system accent={desktop.system_accent()} | wallpaper={os.path.basename(wall) if wall else None} "
        f"| ffmpeg={'yes' if shutil.which('ffmpeg') else 'no'} | heatmap={heatmap_active()}",
        "Config: " + json.dumps({k: v for k, v in cfg.items() if k not in PRIVATE_KEYS + ("custom_css",)},
                                ensure_ascii=False),
        f"Custom CSS: {len(cfg['custom_css'])} chars",
        "Errors:" + ("".join("\n  " + e for e in log.ENTRIES) or " none"),
    ]
    return "\n".join(lines)


def heatmap_active():
    am = mw.addonManager
    return any((d == HEATMAP_ID or "heatmap" in (am.addonName(d) or "").lower()) and am.isEnabled(d)
               for d in am.allAddons())


class ThemeDialog(QDialog):
    def __init__(self, api):
        super().__init__(mw)
        self.setObjectName("ctDialog")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.api = api
        self.defaults = api.defaults()
        self.cfg = api.load_config()
        self._loading = False
        self._styled_accent = None
        self.setWindowTitle(t("title"))
        self.resize(1240, 780)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._render_preview)

        self._build()
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    # ---------- Aufbau ----------

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        root.addWidget(split, 1)

        # links: Navigation + Seiten
        left = QWidget()
        lh = QHBoxLayout(left)
        lh.setContentsMargins(0, 0, 0, 0)
        lh.setSpacing(12)
        self.nav = QListWidget()
        self.nav.setObjectName("ctNav")
        self.nav.setFixedWidth(150)
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pages = QStackedWidget()
        builders = {"designs": self._page_designs, "look": self._page_look, "cards": self._page_cards, "shape": self._page_shape, "text": self._page_text,
                    "areas": self._page_areas,
                    "study": self._page_study, "addons": self._page_addons, "advanced": self._page_advanced}
        for key in PAGES:
            self.nav.addItem(t("page_" + key))
            self.pages.addWidget(self._page(t("page_" + key), builders[key]()))
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)
        lh.addWidget(self.nav)
        lh.addWidget(self.pages, 1)
        left.setMinimumWidth(560)
        split.addWidget(left)

        # rechts: Vorschau in einer Karte
        frame = QFrame()
        frame.setObjectName("ctPreviewFrame")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(12, 12, 12, 12)
        self.preview = ThemePreview(t, self.api)
        fl.addWidget(self.preview)
        split.addWidget(frame)
        split.setSizes([660, 600])

        # unten: Aktionen
        bar = QHBoxLayout()
        b_reset = QPushButton(t("reset"))
        b_reset.setObjectName("ctGhost")
        b_reset.clicked.connect(self._reset)
        bar.addWidget(b_reset)
        bar.addStretch()
        b_cancel = QPushButton(t("cancel"))
        b_cancel.clicked.connect(self.reject)
        b_apply = QPushButton(t("apply"))
        b_apply.clicked.connect(self._apply)
        b_save = QPushButton(t("save"))
        b_save.setObjectName("ctPrimary")
        b_save.setDefault(True)
        b_save.clicked.connect(self._ok)
        for b in (b_cancel, b_apply, b_save):
            bar.addWidget(b)
        root.addLayout(bar)

    def _page(self, title, sections):
        page = QWidget()
        page.setObjectName("ctPage")
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 6, 0)
        v.setSpacing(12)
        lbl = QLabel(title)
        lbl.setObjectName("ctPageTitle")
        v.addWidget(lbl)
        for s in sections:
            v.addWidget(s)
        v.addStretch()
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setWidget(page)
        return sa

    def _slider(self, lo, hi, suffix=""):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        val = QLabel()
        val.setObjectName("ctHint")
        val.setMinimumWidth(46)
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        s.valueChanged.connect(lambda v: val.setText(f"{v}{suffix}"))
        s.valueChanged.connect(self._changed)
        lay.addWidget(s, 1)
        lay.addWidget(val)
        box.slider = s
        return box

    def _combo(self, items):
        c = QComboBox()
        # nicht auf den längsten Eintrag aufblähen, sonst wird die Spalte breiter als sichtbar
        c.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        c.setMinimumContentsLength(8)
        c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ui.modern_popup(c)
        for key, label in items:
            c.addItem(label, key)
        c.currentIndexChanged.connect(self._changed)
        return c

    def _toggle(self, text):
        c = Toggle(text)
        c.toggled.connect(self._changed)
        return c

    def _pack_icon(self, key, pack):
        """Vorschaubild: das Wallpaper, bei Musterpaketen eine Farbfläche mit Akzentpunkt."""
        size = QSize(124, 70)
        if pack.get("art"):
            from PyQt6.QtSvg import QSvgRenderer
            from . import art
            pm = QPixmap(size)
            p = QPainter(pm)
            p.setClipRect(pm.rect())
            # feine Linienmotive sind im Dunkeln als kleines Bild kaum zu erkennen
            svg = art.wallpaper_svg(pack["art"], pack["accent"], pack["art"] not in ("topo", "flow", "seigaiha", "clouds"))
            # Seitenverhältnis wie "slice": auf Breite skalieren, vertikal zentrieren
            h = size.width() * art.H / art.W
            QSvgRenderer(QByteArray(svg.encode())).render(p, QRectF(0, (size.height() - h) / 2, size.width(), h))
            p.end()
            return QIcon(pm)
        if pack.get("wallpaper_dark"):
            # Hell/Dunkel-Paar: links das helle, rechts das dunkle Bild
            pm = QPixmap(size)
            p = QPainter(pm)
            for i, key in enumerate(("wallpaper", "wallpaper_dark")):
                thumb = QPixmap(os.path.join(ADDON_DIR, "wallpapers", pack[key].replace(".jpg", "_thumb.jpg")))
                half = thumb.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                w = size.width() // 2
                p.drawPixmap(i * w, 0, half, (half.width() - size.width()) // 2 + i * w, 0, w, size.height())
            p.end()
            return QIcon(pm)
        if pack.get("wallpaper"):
            thumb = os.path.join(ADDON_DIR, "wallpapers", pack["wallpaper"].replace(".jpg", "_thumb.jpg"))
            return QIcon(QPixmap(thumb).scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                              Qt.TransformationMode.SmoothTransformation))
        if pack.get("omarchy"):
            # Farbthema: Hintergrund des Themes mit seiner Palette als Streifen
            pm = QPixmap(size)
            pm.fill(QColor(pack["bg_light"] if pack.get("om_light") else pack["bg_dark"]))
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            cols = pack.get("palette") or [pack["accent"]]
            w = size.width() / len(cols)
            for i, c in enumerate(cols):
                p.fillRect(QRectF(i * w, size.height() * .62, w + 1, size.height() * .38), QColor(c))
            p.setBrush(QColor(pack["accent"]))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(size.width() / 2, size.height() * .32), 13, 13)
            p.end()
            return QIcon(pm)
        # Musterpaket: helle Fläche mit Lichtschein in Akzentfarbe und dem Muster als Punkte
        def color(alpha):  # QColor versteht kein CSS-rgba(), daher Hex + Alpha
            c = QColor(pack["accent"])
            c.setAlphaF(alpha)
            return c

        pm = QPixmap(size)
        pm.fill(QColor(pack["bg_light"]))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QRadialGradient(QPointF(size.width() / 2, -10), size.width() * .7)
        glow.setColorAt(0, color(.45))
        glow.setColorAt(1, color(0))
        p.fillRect(pm.rect(), glow)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color(.55))
        for x in range(8, size.width(), 12):
            for y in range(8, size.height(), 12):
                p.drawEllipse(QPointF(x, y), 1.3, 1.3)
        p.end()
        return QIcon(pm)

    def _tile(self, text, icon, on_click):
        b = QToolButton()
        b.setText(text)
        b.setIcon(icon)
        b.setIconSize(QSize(124, 70))
        b.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        b.setCheckable(True)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        # darf schmaler werden als sein Inhalt, sonst wird die Spalte breiter als sichtbar
        b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        b.setMinimumSize(90, 108)
        b.setObjectName("ctPack")
        b.clicked.connect(on_click)
        return b

    def _page_designs(self):
        self.pack_buttons = {}
        names = t("pack_names")
        groups = (("packs_art", lambda p: p.get("art")), ("packs_photo", lambda p: p.get("wallpaper")),
                  ("packs_omarchy", lambda p: p.get("omarchy")),
                  ("packs_pattern", lambda p: not p.get("art") and not p.get("wallpaper") and not p.get("omarchy")))
        sections = []
        for title, test in groups:
            hint = t("packs_hint") if not sections else (t("packs_omarchy_hint") if title == "packs_omarchy" else None)
            sec = Section(t(title), hint)
            grid = QGridLayout()
            grid.setSpacing(10)
            for i, (key, pack) in enumerate((k, p) for k, p in theme.PACKS.items() if test(p)):
                b = self._tile(names.get(key) or pack.get("title", key), self._pack_icon(key, pack),
                               lambda _=False, k=key: self._apply_pack(k))
                grid.addWidget(b, i // 3, i % 3)
                self.pack_buttons[key] = b
            sec.form.addRow(grid)
            sections.append(sec)

        mine = Section(t("my_designs"), t("my_designs_hint"))
        row = QGridLayout()  # 2x2 statt einer langen Zeile, sonst wird die Seite breiter als sichtbar
        row.setSpacing(8)
        for i, (label, slot) in enumerate(((t("save_design"), self._save_design), (t("design_from_image"), self._design_from_image),
                                           (t("gallery_open"), self._open_gallery), (t("import_design"), self._import_design))):
            b = QPushButton(label)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            b.clicked.connect(slot)
            row.addWidget(b, i // 2, i % 2)
        mine.form.addRow(row)
        self.design_grid = QGridLayout()
        self.design_grid.setSpacing(10)
        mine.form.addRow(self.design_grid)
        self.design_empty = QLabel(t("no_designs"))
        self.design_empty.setObjectName("ctHint")
        self.design_empty.setWordWrap(True)
        mine.form.addRow(self.design_empty)
        gallery = QLabel(t("gallery_hint"))
        gallery.setObjectName("ctHint")
        gallery.setWordWrap(True)
        gallery.setOpenExternalLinks(True)
        mine.form.addRow(gallery)
        self.design_buttons = {}
        self._refresh_designs()
        return [mine] + sections

    def _refresh_designs(self):
        from . import designs
        while self.design_grid.count():
            w = self.design_grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.design_buttons = {}
        items = designs.list_designs()
        for i, (did, data, folder) in enumerate(items):
            thumb = os.path.join(folder, "thumb.jpg")
            if os.path.isfile(thumb):
                icon = QIcon(QPixmap(thumb).scaled(QSize(124, 70), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                   Qt.TransformationMode.SmoothTransformation))
            else:
                icon = self._pack_icon(did, {"accent": data["settings"].get("accent", "#888888"),
                                             "bg_light": data["settings"].get("bg_light", "#f5f5f5"),
                                             "bg_dark": data["settings"].get("bg_dark", "#151515")})
            b = self._tile(data.get("name", did), icon, lambda _=False, d=did: self._apply_design(d))
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda _pos, d=did, w=b: self._design_menu(d, w))
            b.setToolTip(t("design_tip"))
            self.design_grid.addWidget(b, i // 3, i % 3)
            self.design_buttons[did] = b
        self.design_empty.setVisible(not items)
        self._update_presets()

    def _design_menu(self, did, widget):
        from . import designs
        menu = QMenu(self)
        menu.addAction(t("apply_design"), lambda: self._apply_design(did))
        menu.addAction(t("export_design"), lambda: self._export_design(did))
        menu.addSeparator()
        menu.addAction(t("delete_design"), lambda: (designs.delete_design(did), self._refresh_designs()))
        menu.exec(widget.mapToGlobal(widget.rect().bottomLeft()))

    def _ask_name(self, default):
        name, ok = QInputDialog.getText(self, t("my_designs"), t("design_name"), text=default)
        return name.strip() if ok and name.strip() else None

    def _save_design(self):
        from . import designs
        name = self._ask_name(t("my_design_default"))
        if name:
            self.cfg = self._collect()
            self.cfg["design"] = designs.save_design(name, self.cfg)
            self._refresh_designs()
            tooltip(t("design_saved"), parent=self)

    def _design_from_image(self):
        from . import designs

        def chosen(path):
            if not path:
                return
            name = self._ask_name(os.path.splitext(os.path.basename(path))[0][:40])
            if not name:
                return
            look = designs.design_from_image(path, name, self._collect())
            if not look:
                showWarning(f"{t('import_err')}\n{path}", parent=self)
                return
            self.cfg = look
            self._load_into_widgets()
            self._restyle()
            self._render_preview()
            self._refresh_designs()

        exts = " ".join("*" + e for e in desktop.IMAGE_EXTS)
        getFile(self, t("design_from_image"), cb=chosen, filter=exts, key="deckorator_design_image")

    def _open_gallery(self):
        from .gallery import GalleryDialog

        def on_design(look):
            self.cfg = look
            self._load_into_widgets()
            self._restyle()
            self._render_preview()
            self._refresh_designs()

        GalleryDialog(self, t, self._collect, on_design).exec()

    def _apply_design(self, did):
        from . import designs
        try:
            self.cfg = designs.apply_design(did, self._collect())
        except (OSError, ValueError) as e:
            showWarning(f"{t('import_err')}\n{e}", parent=self)
            return
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _export_design(self, did):
        from . import designs
        path = getSaveFile(self, t("export_design"), "deckorator_design_export", "Deckorator", ".deckorator",
                           f"{did}.deckorator")
        if path:
            designs.export_design(did, path)
            tooltip(t("design_exported"), parent=self)

    def _import_design(self):
        from . import designs

        def chosen(path):
            if not path:
                return
            try:
                designs.import_design(path)
            except Exception as e:
                showWarning(f"{t('import_err')}\n{e}", parent=self)
                return
            self._refresh_designs()

        getFile(self, t("import_design"), cb=chosen, filter="*.deckorator *.zip", key="deckorator_design_export")

    def _page_cards(self):
        from . import cards
        styles = Section(t("card_styles"), t("card_styles_hint"))
        grid = QGridLayout()
        grid.setSpacing(10)
        self.card_style_buttons = {}
        names = t("card_style_names")
        for i, key in enumerate(cards.STYLES):
            b = QPushButton(names[key])
            b.setCheckable(True)
            b.setMinimumHeight(44)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda _=False, k=key: self._select_card_style(k))
            grid.addWidget(b, i // 3, i % 3)
            self.card_style_buttons[key] = b
        styles.form.addRow(grid)

        target = Section(t("card_target"), t("card_target_hint"))
        self.card_deck = QComboBox()
        self.card_deck.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.card_deck.addItem(t("card_pick_deck"), None)
        for d in sorted(mw.col.decks.all_names_and_ids(), key=lambda d: d.name):
            self.card_deck.addItem(d.name, d.id)
        self.card_deck.currentIndexChanged.connect(self._card_deck_chosen)
        ui.modern_popup(self.card_deck)
        target.row(t("card_by_deck"), self.card_deck)
        self.card_types = QListWidget()
        self.card_types.setMinimumHeight(170)
        target.row(self.card_types)
        actions = QHBoxLayout()
        b_apply = QPushButton(t("card_apply"))
        b_apply.setObjectName("ctPrimary")
        b_apply.clicked.connect(self._apply_card_style_to_types)
        b_remove = QPushButton(t("card_remove"))
        b_remove.clicked.connect(self._remove_card_style)
        actions.addWidget(b_apply)
        actions.addWidget(b_remove)
        actions.addStretch()
        target.form.addRow(actions)
        self._fill_card_types()
        return [styles, target]

    def _fill_card_types(self, checked=None):
        from . import cards
        names = t("card_style_names")
        self.card_types.clear()
        for ntid, name, count, style in cards.note_types():
            label = t("card_type_row").format(name=name, count=count)
            if style:
                label += " · " + names.get(style, style)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, ntid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if checked and ntid in checked else Qt.CheckState.Unchecked)
            self.card_types.addItem(item)

    def _checked_types(self):
        return [self.card_types.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.card_types.count())
                if self.card_types.item(i).checkState() == Qt.CheckState.Checked]

    def _card_deck_chosen(self):
        from . import cards
        did = self.card_deck.currentData()
        if did:
            self._fill_card_types(cards.note_types_in_deck(did))

    def _select_card_style(self, key):
        for k, b in self.card_style_buttons.items():
            b.setChecked(k == key)
        self.selected_card_style = key
        self.preview.set_card_style(key)

    def _apply_card_style_to_types(self):
        from . import cards
        style = getattr(self, "selected_card_style", None)
        types = self._checked_types()
        if not style or not types:
            tooltip(t("card_need_choice"), parent=self)
            return
        if not askUser(t("card_confirm").format(n=len(types)), parent=self):
            return
        self.cfg = self._collect()
        cards.apply(types, style, self.cfg)
        # damit der Kartenhintergrund des Stils beim Lernen sichtbar ist
        self._set_combo(self.review_background, "note")
        self._apply()
        self._fill_card_types(set(types))
        tooltip(t("card_applied"), parent=self)

    def _remove_card_style(self):
        from . import cards
        types = self._checked_types()
        if not types:
            tooltip(t("card_need_types"), parent=self)
            return
        cards.remove(types)
        self._fill_card_types(set(types))
        self.preview.set_card_style(None)
        tooltip(t("card_removed"), parent=self)

    def _page_look(self):
        presets = Section(t("presets"))
        grid = QGridLayout()
        grid.setSpacing(10)
        names = t("preset_names")
        self.preset_buttons = {}
        for i, (key, p) in enumerate(theme.PRESETS.items()):
            b = QPushButton(names[key])
            b.setCheckable(True)
            b.setMinimumSize(60, 52)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            a = p["accent"]
            b.setStyleSheet(
                "QPushButton { color: white; font-weight: 600; border-radius: 12px; border: 2px solid transparent; padding: 0 4px;"
                f" background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {theme._mix(a, '#ffffff', .12)},"
                f" stop:1 {theme._mix(a, '#000000', .28)}); }}"
                "QPushButton:hover { border: 2px solid rgba(255,255,255,.55); }"
                "QPushButton:checked { border: 3px solid palette(window-text); }")
            b.clicked.connect(lambda _=False, k=key: self._apply_preset(k))
            grid.addWidget(b, i // 4, i % 4)
            self.preset_buttons[key] = b
            b.setMinimumSize(60, 44)
        presets.form.addRow(grid)

        colors = Section(t("colors"))
        src = QHBoxLayout()
        self.accent_source = self._combo([("manual", t("src_manual")), ("system", t("src_system")),
                                          ("wallpaper", t("src_wallpaper"))])
        self.accent_source.currentIndexChanged.connect(lambda _: None if self._loading else self._detect_accent())
        self.b_redetect = QPushButton(t("redetect"))
        self.b_redetect.clicked.connect(self._detect_accent)
        src.addWidget(self.accent_source, 1)
        src.addWidget(self.b_redetect)
        colors.form.addRow(t("accent_source"), src)
        self.accent_info = QLabel()
        self.accent_info.setObjectName("ctHint")
        self.accent_info.setWordWrap(True)
        colors.row(self.accent_info)
        swatches = QGridLayout()
        swatches.setSpacing(6)
        for i, col in enumerate(theme.SWATCHES):
            s = QPushButton()
            s.setFixedSize(26, 26)
            s.setCursor(Qt.CursorShape.PointingHandCursor)
            s.setToolTip(col.upper())
            s.setStyleSheet(f"QPushButton {{ background: {col}; border: 2px solid rgba(128,128,128,.35); border-radius: 13px; padding: 0; }}"
                            "QPushButton:hover { border: 2px solid palette(window-text); }")
            s.clicked.connect(lambda _=False, c=col: self._pick_accent(c))
            swatches.addWidget(s, i // 12, i % 12)
        colors.form.addRow(t("quick_colors"), swatches)
        self.accent = ColorButton("#000000")
        self.bg_light = ColorButton("#ffffff")
        self.bg_dark = ColorButton("#000000")
        for cb in (self.accent, self.bg_light, self.bg_dark):
            cb.changed.connect(self._custom_changed)
        # die Hintergrundfarben wirken nur im jeweiligen Modus, also die Vorschau dorthin schalten
        self.bg_light.changed.connect(lambda: self.preview.set_night(False))
        self.bg_dark.changed.connect(lambda: self.preview.set_night(True))
        colors.row(t("accent"), self.accent)
        colors.row(t("bg_light"), self.bg_light)
        colors.row(t("bg_dark"), self.bg_dark)

        bg = Section(t("background"))
        self.bg_style = self._combo([(s, t("style_" + s)) for s in theme.BACKGROUND_STYLES])
        self.bg_style.currentIndexChanged.connect(self._style_changed)
        bg.row(t("bg_style"), self.bg_style)
        from . import art
        art_names = t("art_names")
        self.art = self._combo([(n, art_names[n]) for n in art.ART])
        self.art_label = QLabel(t("art_motif"))
        bg.form.addRow(self.art_label, self.art)
        self.desktop_info = QLabel()
        self.desktop_info.setObjectName("ctHint")
        self.desktop_info.setWordWrap(True)
        bg.row(self.desktop_info)
        self.bg_intensity = bg.row(t("bg_intensity"), self._slider(0, 100, " %"))
        img = QHBoxLayout()
        img.setContentsMargins(0, 0, 0, 0)
        self.bg_image_label = QLabel()
        self.bg_image_label.setObjectName("ctHint")
        self.bg_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        b_choose = QPushButton(t("choose"))
        b_choose.clicked.connect(self._choose_image)
        self.b_remove = QPushButton(t("remove"))
        self.b_remove.clicked.connect(self._remove_image)
        img.addWidget(self.bg_image_label, 1)
        img.addWidget(b_choose)
        img.addWidget(self.b_remove)
        self.img_row = QWidget()
        self.img_row.setLayout(img)
        bg.row(t("bg_image"), self.img_row)
        drow = QHBoxLayout()
        drow.setContentsMargins(0, 0, 0, 0)
        self.dark_image_label = QLabel()
        self.dark_image_label.setObjectName("ctHint")
        self.dark_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        b_dark = QPushButton(t("choose"))
        b_dark.clicked.connect(self._choose_dark_image)
        b_dark_rm = QPushButton(t("remove"))
        b_dark_rm.clicked.connect(lambda: self._set_cfg(bg_image_dark=""))
        for w in (self.dark_image_label, b_dark, b_dark_rm):
            drow.addWidget(w, 1 if w is self.dark_image_label else 0)
        self.dark_row = QWidget()
        self.dark_row.setLayout(drow)
        self.dark_row.setToolTip(t("bg_image_dark_hint"))
        bg.row(t("bg_image_dark"), self.dark_row)
        self.bg_form = bg.form

        banner = Section(t("banner"), t("banner_hint"))
        items = [("", t("banner_none"))]
        items += [(f"art:{n}", t("banner_art").format(name=art_names[n])) for n in art.ART]
        pack_names = t("pack_names")
        items += [(f"photo:{k}", t("banner_photo").format(name=pack_names[k]))
                  for k, pk in theme.PACKS.items() if pk.get("wallpaper")]
        items += [("image", t("banner_image"))]
        self.banner = banner.row(t("banner_motif"), self._combo(items))
        self.banner.currentIndexChanged.connect(self._update_enabled)
        self.banner_area = banner.row(t("banner_area"), self._combo(
            [("bar", t("ba_bar")), ("capsule", t("ba_capsule"))]))
        self.banner_height = banner.row(t("banner_height"), self._combo(
            [("small", t("bh_small")), ("medium", t("bh_medium")), ("large", t("bh_large"))]))
        brow = QHBoxLayout()
        brow.setContentsMargins(0, 0, 0, 0)
        self.banner_image_label = QLabel()
        self.banner_image_label.setObjectName("ctHint")
        self.banner_image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        b_banner = QPushButton(t("choose"))
        b_banner.clicked.connect(self._choose_banner)
        brow.addWidget(self.banner_image_label, 1)
        brow.addWidget(b_banner)
        self.banner_row = QWidget()
        self.banner_row.setLayout(brow)
        banner.row(t("banner_image"), self.banner_row)
        self.banner_form = banner.form
        return [presets, colors, bg, banner]

    def _page_shape(self):
        glass = Section(t("glass_title"), t("glass_hint"))
        self.glass = self._toggle(t("glass"))
        self.glass.toggled.connect(self._update_enabled)
        glass.row(self.glass)
        self.blur = glass.row(t("blur"), self._slider(0, 40, " px"))
        self.opacity = glass.row(t("opacity"), self._slider(10, 100, " %"))

        self.glow = self._toggle(t("glow"))
        glass.row(self.glow)

        shapes = Section(t("shapes"))
        self.radius = shapes.row(t("radius"), self._slider(0, 32, " px"))
        self.button_shape = shapes.row(t("buttons"), self._combo(
            [("pill", t("btn_pill")), ("rounded", t("btn_rounded")), ("square", t("btn_square"))]))
        self.shadow = shapes.row(t("shadow"), self._combo(list(enumerate(t("shadow_levels")))))

        bars = Section(t("bars"))
        self.toolbar_style = bars.row(t("toolbar"), self._combo([("floating", t("tb_floating")), ("flat", t("tb_flat"))]))
        self.compact = self._toggle(t("compact"))
        bars.row(self.compact)

        perf = Section(t("performance"))
        self.performance = perf.row(t("perf_mode"), self._combo(
            [("auto", t("perf_auto")), ("full", t("perf_full")), ("light", t("perf_light"))]))
        self.performance.currentIndexChanged.connect(self._update_enabled)
        self.perf_info = QLabel(self._hardware_text())
        self.perf_info.setObjectName("ctHint")
        self.perf_info.setWordWrap(True)
        perf.row(self.perf_info)
        return [perf, glass, shapes, bars]

    def _page_areas(self):
        from . import windows
        home = Section(t("areas_home"), t("areas_hint"))
        two = [("on", t("mode_on")), ("original", t("mode_original"))]
        self.area_modes = {}
        for key in ("main", "review_bar"):
            self.area_modes[key] = home.row(t("area_" + key), self._combo(two))
        self.area_modes["other"] = home.row(t("area_other"), self._combo(
            [("on", t("mode_colors")), ("original", t("mode_original"))]))
        wins = Section(t("areas_windows"))
        three = [("bold", t("mode_bold")), ("subtle", t("mode_subtle")), ("original", t("mode_original"))]
        for kind in windows.WINDOW_KINDS:
            self.area_modes[kind] = wins.row(t("area_" + kind), self._combo(three))
            self.area_modes[kind].currentIndexChanged.connect(
                lambda _: None if self._loading else self.preview.set_view("windows"))
        h = QHBoxLayout()
        for label, mode in ((t("all_bold"), "bold"), (t("all_original"), "original")):
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, m=mode: self._set_all_areas(m))
            h.addWidget(b)
        h.addStretch()
        wins.form.addRow(h)
        return [home, wins]

    def _set_all_areas(self, mode):
        for key, combo in self.area_modes.items():
            self._set_combo(combo, mode if combo.findData(mode) >= 0 else ("on" if mode != "original" else "original"))

    def _hardware_text(self):
        hw = self.api.hardware()
        facts = []
        if hw["software"]:
            facts.append(t("hw_software"))
        if hw["threads"]:
            facts.append(t("hw_threads").format(n=hw["threads"]))
        if hw["ram"]:
            facts.append(t("hw_ram").format(n=round(hw["ram"])))
        if hw["battery"]:
            facts.append(t("hw_battery"))
        verdict = t("hw_weak") if hw["weak"] else t("hw_strong")
        return t("hw_detected").format(facts=", ".join(facts), verdict=verdict)

    def _page_text(self):
        sec = Section(t("font"), t("font_hint"))
        self.font_default = self._toggle(t("font_default"))
        self.font_default.toggled.connect(self._update_enabled)
        sec.row(self.font_default)
        self.font_family = QFontComboBox()
        self.font_family.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.font_family.setMinimumContentsLength(8)
        ui.modern_popup(self.font_family, own_delegate=False)
        self.font_family.currentFontChanged.connect(self._changed)
        sec.row(t("font"), self.font_family)
        self.font_scale = sec.row(t("font_scale"), self._slider(80, 140, " %"))
        return [sec]

    def _page_study(self):
        bg = Section(t("review_bg"), t("rb_hint"))
        self.review_background = self._combo(
            [("calm", t("rb_calm")), ("full", t("rb_full")), ("note", t("rb_note"))])
        self.review_background.currentIndexChanged.connect(
            lambda _: None if self._loading else self.preview.set_view("study"))
        bg.row(self.review_background)
        display = Section(t("display"))
        self.colored_answers = self._toggle(t("answers"))
        self.count_badges = self._toggle(t("badges"))
        self.highlight_today = self._toggle(t("highlight_today"))
        self.highlight_today.toggled.connect(lambda _: None if self._loading else self.preview.set_view("home"))
        display.row(self.highlight_today)
        display.row(self.colored_answers)
        display.row(self.count_badges)
        return [bg, display]

    def _page_addons(self):
        hint = t("hm_hint") if heatmap_active() else t("hm_missing")
        sec = Section(t("heatmap"), hint)
        self.heatmap_style = sec.row(t("hm_style"), self._combo(
            [("theme", t("hm_theme")), ("colors", t("hm_colors")), ("original", t("hm_original"))]))
        self.heatmap_style.currentIndexChanged.connect(
            lambda _: None if self._loading else self.preview.set_view("home"))
        center = Section(t("addon_center"), t("addon_center_hint"))
        self.addon_center = self._toggle(t("addon_center_on"))
        center.row(self.addon_center)
        embed = Section(t("embed_title"), t("embed_hint"))
        self.embed_addons = self._toggle(t("embed_on"))
        self.embed_addons.toggled.connect(lambda _: None if self._loading else self.preview.set_view("home"))
        embed.row(self.embed_addons)
        from . import conflicts
        found = conflicts.find(self.api.MODULE)
        conf = Section(t("conflicts_title"), t("conflicts_found").format(names=", ".join(n for _d, n in found))
                       if found else t("conflicts_none"))
        return [sec, center, embed, conf]

    def _page_advanced(self):
        motion = Section(t("motion"), t("motion_hint"))
        self.animations = self._toggle(t("animations"))
        motion.row(self.animations)
        css = Section(t("custom_css"), t("custom_css_hint"))
        self.custom_css = QPlainTextEdit()
        self.custom_css.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.custom_css.setPlaceholderText("html body .hitem { letter-spacing: .02em; }")
        self.custom_css.setMinimumHeight(140)
        self.custom_css.textChanged.connect(self._changed)
        css.row(self.custom_css)
        share = Section(t("share"), t("share_hint"))
        h = QHBoxLayout()
        b_exp = QPushButton(t("export"))
        b_exp.clicked.connect(self._export)
        b_imp = QPushButton(t("import"))
        b_imp.clicked.connect(self._import)
        h.addWidget(b_exp)
        h.addWidget(b_imp)
        h.addStretch()
        share.form.addRow(h)

        help_ = Section(t("help"), t("help_hint"))
        b_diag = QPushButton(t("copy_diag"))
        b_diag.clicked.connect(self._copy_diagnostics)
        hh = QHBoxLayout()
        hh.addWidget(b_diag)
        hh.addStretch()
        help_.form.addRow(hh)
        return [motion, css, share, help_]

    def _copy_diagnostics(self):
        QApplication.clipboard().setText(diagnostics(self.api, self._collect()))
        tooltip(t("diag_copied"), parent=self)

    # ---------- Werte <-> Widgets ----------

    @staticmethod
    def _set_combo(combo, key):
        i = combo.findData(key)
        combo.setCurrentIndex(max(0, i))

    def _load_into_widgets(self):
        c = self.cfg
        self._loading = True
        self._set_combo(self.accent_source, c["accent_source"])
        self.accent.set_color(c["accent"])
        self.bg_light.set_color(c["bg_light"])
        self.bg_dark.set_color(c["bg_dark"])
        self._set_combo(self.bg_style, c["background"])
        self.bg_intensity.slider.setValue(c["bg_intensity"])
        self.glass.setChecked(c["glass"])
        self.blur.slider.setValue(c["blur"])
        self.opacity.slider.setValue(c["glass_opacity"])
        self.radius.slider.setValue(c["radius"])
        self._set_combo(self.button_shape, c["button_shape"])
        self._set_combo(self.shadow, c["shadow"])
        self._set_combo(self.toolbar_style, c["toolbar_style"])
        self._set_combo(self.performance, c["performance"])
        self.compact.setChecked(c["compact"])
        self.glow.setChecked(c.get("glow", True))
        self.font_default.setChecked(not c["font_family"])
        # ohne eigene Schrift die Anki-Schrift vorauswählen, nicht den ersten Eintrag der Liste
        self.font_family.setCurrentFont(QFont(c["font_family"] or mw.web.font().family()))
        self.font_scale.slider.setValue(c["font_scale"])
        self.count_badges.setChecked(c["count_badges"])
        self.colored_answers.setChecked(c["colored_answers"])
        self.animations.setChecked(c["animations"])
        self.highlight_today.setChecked(c["highlight_today"])
        self.addon_center.setChecked(c.get("addon_center", True))
        self.embed_addons.setChecked(c.get("embed_addons", True))
        self._set_combo(self.review_background, c["review_background"])
        self._set_combo(self.heatmap_style, c["heatmap_style"])
        from . import windows
        for key, combo in self.area_modes.items():
            if key in windows.WINDOW_KINDS:
                self._set_combo(combo, windows.window_mode(c, key))
            else:
                self._set_combo(combo, "on" if c["areas"].get(key, key != "other") else "original")
        self._set_combo(self.art, c.get("art", "fuji"))
        self._set_combo(self.banner, c.get("banner", ""))
        self._set_combo(self.banner_height, c.get("banner_height", "medium"))
        self._set_combo(self.banner_area, c.get("banner_area", "bar"))
        self.custom_css.setPlainText(c["custom_css"])
        self._update_image_label()
        self._update_presets()
        self._loading = False
        self._update_enabled()

    def _collect(self):
        c = dict(self.cfg)
        c.update({
            "accent_source": self.accent_source.currentData(),
            "accent": self.accent.color(), "bg_light": self.bg_light.color(), "bg_dark": self.bg_dark.color(),
            "background": self.bg_style.currentData(), "bg_intensity": self.bg_intensity.slider.value(),
            "glass": self.glass.isChecked(), "blur": self.blur.slider.value(),
            "glass_opacity": self.opacity.slider.value(), "radius": self.radius.slider.value(),
            "button_shape": self.button_shape.currentData(), "shadow": self.shadow.currentData(),
            "toolbar_style": self.toolbar_style.currentData(), "compact": self.compact.isChecked(), "glow": self.glow.isChecked(),
            "performance": self.performance.currentData(),
            "font_family": "" if self.font_default.isChecked() else self.font_family.currentFont().family(),
            "font_scale": self.font_scale.slider.value(),
            "count_badges": self.count_badges.isChecked(), "colored_answers": self.colored_answers.isChecked(),
            "animations": self.animations.isChecked(),
            "highlight_today": self.highlight_today.isChecked(),
            "addon_center": self.addon_center.isChecked(), "embed_addons": self.embed_addons.isChecked(),
            "review_background": self.review_background.currentData(),
            "heatmap_style": self.heatmap_style.currentData(),
            **self._collect_areas(),
            "art": self.art.currentData(), "banner": self.banner.currentData(),
            "banner_height": self.banner_height.currentData(), "banner_area": self.banner_area.currentData(),
            "custom_css": self.custom_css.toPlainText(),
        })
        return c

    def _collect_areas(self):
        from . import windows
        areas = dict(self.cfg.get("areas", {}))
        styles = dict(self.cfg.get("window_styles", {}))
        for key, combo in self.area_modes.items():
            mode = combo.currentData()
            areas[key] = mode != "original"
            if key in windows.WINDOW_KINDS and mode != "original":
                styles[key] = mode
        return {"areas": areas, "window_styles": styles}

    def _set_cfg(self, **values):
        self.cfg = self._collect()
        self.cfg.update(values)
        self._load_into_widgets()
        self._render_preview()

    def _choose_dark_image(self):
        def chosen(path):
            if path:
                name = desktop.prepare_image(path, USER_DIR, "background_dark")
                if name:
                    self._set_cfg(bg_image_dark=name, background="image")

        exts = " ".join("*" + e for e in desktop.IMAGE_EXTS)
        getFile(self, t("bg_image_dark"), cb=chosen, filter=exts, key="deckorator_bg_dark")

    def _choose_banner(self):
        def chosen(path):
            if not path:
                return
            name = desktop.prepare_image(path, USER_DIR, "banner")
            if not name:
                showWarning(f"{t('import_err')}\n{path}", parent=self)
                return
            self.cfg = self._collect()
            self.cfg.update(banner_image=name, banner="image")
            self._load_into_widgets()
            self._render_preview()

        exts = " ".join("*" + e for e in desktop.IMAGE_EXTS)
        getFile(self, t("banner_image"), cb=chosen, filter=exts, key="deckorator_banner")

    def _update_enabled(self):
        manual = self.accent_source.currentData() == "manual"
        self.accent.setEnabled(manual)
        self.b_redetect.setVisible(not manual)
        self.accent_info.setVisible(not manual)
        if not manual and not self.accent_info.text():
            self.accent_info.setText(t("src_hint"))
        style = self.bg_style.currentData()
        # Zeilen samt Beschriftung nur zeigen, wenn sie gerade etwas bewirken
        self.bg_form.setRowVisible(self.img_row, style == "image")
        self.bg_form.setRowVisible(self.dark_row, style == "image")
        self.dark_image_label.setText(self.cfg.get("bg_image_dark") or t("none"))
        self.bg_intensity.setEnabled(style != "solid")
        self.desktop_info.setVisible(style == "desktop")
        self.art.setVisible(style == "art")
        self.art_label.setVisible(style == "art")
        has_banner = bool(self.banner.currentData())
        self.banner_height.setEnabled(has_banner)
        self.banner_area.setEnabled(has_banner)
        self.banner_form.setRowVisible(self.banner_row, self.banner.currentData() == "image")
        self.banner_image_label.setText(self.cfg.get("banner_image") or t("none"))
        if style == "desktop" and not self.desktop_info.text():
            self._update_desktop_info()
        light = self.performance.currentData() == "light" or (
            self.performance.currentData() == "auto" and self.api.hardware()["weak"])
        self.blur.setEnabled(self.glass.isChecked() and not light)
        self.opacity.setEnabled(self.glass.isChecked())
        self.font_family.setEnabled(not self.font_default.isChecked())

    def _update_presets(self):
        # beim Aufbau existieren noch nicht alle Knöpfe (Designs-Seite kommt zuerst)
        for k, b in getattr(self, "preset_buttons", {}).items():
            b.setChecked(k == self.cfg.get("preset"))
        for k, b in getattr(self, "pack_buttons", {}).items():
            b.setChecked(k == self.cfg.get("pack"))
        for k, b in getattr(self, "design_buttons", {}).items():
            b.setChecked(k == self.cfg.get("design"))

    def _update_image_label(self):
        name = self.cfg.get("bg_image") or ""
        self.bg_image_label.setText(name or t("none"))
        self.b_remove.setEnabled(bool(name))

    def _restyle(self):
        """Stylesheet nur neu setzen, wenn sich die Akzentfarbe geändert hat."""
        accent = self.cfg["accent"]
        if accent == self._styled_accent:
            return
        self._styled_accent = accent
        colors = ui.palette(accent, theme_manager.night_mode)
        ui.COLORS.clear()
        ui.COLORS.update(colors)
        self.setStyleSheet(ui.stylesheet(colors))

    # ---------- Aktionen ----------

    def _changed(self, *_):
        if self._loading:
            return
        self.cfg = self._collect()
        self._restyle()
        self._timer.start()

    def _custom_changed(self):
        self.cfg["preset"] = ""
        self.cfg["pack"] = ""
        self.cfg["design"] = ""
        self._update_presets()
        self._changed()

    def _apply_pack(self, key):
        # nur echte Einstellungen übernehmen, keine Anzeige-Daten des Pakets
        pack = {k: v for k, v in theme.PACKS[key].items() if k not in ("omarchy", "om_light", "title", "palette")}
        wallpaper = pack.pop("wallpaper", None)
        wallpaper_dark = pack.pop("wallpaper_dark", None)
        self.cfg = self._collect()
        self.cfg.update(pack)
        self.cfg.update(preset="", pack=key, design="", accent_source="manual")
        from . import windows
        if "window_style" in pack:
            self.cfg["window_styles"] = {k: pack["window_style"] for k in windows.WINDOW_KINDS}
        if wallpaper:
            name = desktop.prepare_image(os.path.join(ADDON_DIR, "wallpapers", wallpaper), USER_DIR, "background")
            if name:
                self.cfg["bg_image"] = name
        self.cfg["bg_image_dark"] = ""
        if wallpaper_dark:
            name = desktop.prepare_image(os.path.join(ADDON_DIR, "wallpapers", wallpaper_dark), USER_DIR, "background_dark")
            self.cfg["bg_image_dark"] = name or ""
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _pick_accent(self, color):
        self.cfg = self._collect()
        self.cfg.update(accent=color, accent_source="manual", preset="", pack="", design="")
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _apply_preset(self, key):
        self.cfg = self._collect()
        self.cfg.update(theme.PRESETS[key])
        # ein Klick auf eine Vorlage ist eine bewusste Wahl: automatische Akzentfarbe aus
        self.cfg["accent_source"] = "manual"
        self.cfg["preset"] = key
        self.cfg["pack"] = ""
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _detect_accent(self):
        self.cfg = self._collect()
        source = self.cfg["accent_source"]
        self._update_enabled()
        if source == "manual":
            return
        changes = self.api.sync_desktop(self.cfg, force=True)
        accent = changes.get("accent") or (self.cfg["accent"] if source == "system" and desktop.system_accent() else None)
        if not accent:
            self.accent_info.setText(t("src_failed"))
            return
        where = t("src_system_where") if source == "system" else os.path.basename(
            desktop.wallpaper_path(theme_manager.night_mode) or "")
        self.cfg.update(changes)
        self.cfg["preset"] = ""
        self._load_into_widgets()
        self.accent_info.setText(t("src_found").format(color=accent.upper(), where=where) + "\n" + t("src_hint"))
        self._restyle()
        self._render_preview()

    def _style_changed(self):
        """Beim Wechsel auf "Desktop-Hintergrund" das Wallpaper sofort holen."""
        self._update_enabled()
        if self._loading or self.bg_style.currentData() != "desktop":
            return
        self.cfg = self._collect()
        changes = self.api.sync_desktop(self.cfg, force=True)
        if not changes.get("desktop_image"):
            tooltip(t("no_wallpaper"), parent=self)
            self.desktop_info.setText(t("no_wallpaper"))
            return
        self.cfg.update(changes)
        self._update_desktop_info()
        self._render_preview()

    def _update_desktop_info(self):
        path = desktop.wallpaper_path(theme_manager.night_mode)
        self.desktop_info.setText(t("desktop_hint").format(name=os.path.basename(path)) if path else t("no_wallpaper"))

    def _choose_image(self):
        def chosen(path):
            if not path:
                return
            name = desktop.prepare_image(path, USER_DIR, "background")
            if not name:
                showWarning(f"{t('import_err')}\n{path}", parent=self)
                return
            self.cfg = self._collect()
            self.cfg["bg_image"] = name
            self.cfg["background"] = "image"
            self._load_into_widgets()
            self._render_preview()

        exts = " ".join("*" + e for e in desktop.IMAGE_EXTS)
        getFile(self, t("bg_image"), cb=chosen, filter=exts, key="deckorator_bg")

    def _remove_image(self):
        self.cfg = self._collect()
        self.cfg["bg_image"] = ""
        if self.cfg["background"] == "image":
            self.cfg["background"] = "spotlight"
        self._load_into_widgets()
        self._render_preview()

    def _export(self):
        path = getSaveFile(self, t("export"), "deckorator_export", "Theme", ".json", "deckorator-theme.json")
        if path:
            data = {k: v for k, v in self._collect().items() if k not in PRIVATE_KEYS}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def _import(self):
        def chosen(path):
            if not path:
                return
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("not a JSON object")
            except Exception as e:
                showWarning(f"{t('import_err')}\n{e}", parent=self)
                return
            merged = dict(self.cfg)
            merged.update({k: v for k, v in data.items() if k in self.defaults and k not in PRIVATE_KEYS})
            self.cfg = merged
            self._load_into_widgets()
            self._restyle()
            self._render_preview()

        getFile(self, t("import"), cb=chosen, filter="*.json", key="deckorator_export")

    def _reset(self):
        self.cfg = json.loads(json.dumps(self.defaults))
        self._load_into_widgets()
        self._restyle()
        self._render_preview()

    def _apply(self):
        self.cfg = self._collect()
        self.api.save_config(self.cfg)
        tooltip(t("saved"), parent=self)

    def _ok(self):
        self._apply()
        self.accept()

    def open_page(self, key):
        if key in PAGES:
            self.nav.setCurrentRow(PAGES.index(key))

    def showEvent(self, event):
        super().showEvent(event)
        # Qt setzt den Fokus beim Öffnen sonst ins erste Eingabefeld (die Schriftauswahl) und
        # blättert damit auf die Seite "Schrift"; deshalb Fokus und Seite fest auf die Navigation
        self.nav.setFocus()
        self.pages.setCurrentIndex(self.nav.currentRow())

    def done(self, result):
        # Vorschau-Webansichten freigeben, sonst bleiben sie nach dem Schließen im Speicher
        self._timer.stop()
        self.preview.cleanup()
        super().done(result)

    # ---------- Vorschau ----------

    def _render_preview(self):
        self.preview.set_config(self.cfg)
