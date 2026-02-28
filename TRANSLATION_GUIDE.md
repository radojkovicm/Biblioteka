# Translation Guide — Biblioteka

This guide explains how to add new languages and translations to your Biblioteka application.

## How Translations Work

The application uses a JSON-based translation system with two files:

1. **`frontend/static/translations.json`** — Contains all UI text strings in multiple languages
2. **`app/utils/i18n.py`** — Python module that loads translations and manages localization

## Adding a New Language

### Step 1: Edit `frontend/static/translations.json`

1. Open `frontend/static/translations.json` in a text editor
2. Add a new language object with all translation keys:

```json
{
  "sr": { ... existing Serbian translations ... },
  "en": { ... existing English translations ... },
  "fr": {
    "dashboard": "Tableau de bord",
    "books": "Livres",
    "members": "Membres",
    ... (add all keys from other languages)
  }
}
```

### Step 2: Add Language to Settings

The language will automatically appear in Settings → General after:

1. Database recognizes the new language
2. User selects it from the dropdown

To add it to the language dropdown in settings.html:
```html
<select id="setting-language" class="form-control">
    <option value="sr">Srpski</option>
    <option value="en">English</option>
    <option value="fr">Français</option>
</select>
```

### Step 3: Update Application

The application will:
- Automatically load the new language from `translations.json`
- Make it available in `/settings/public/config` API endpoint
- Allow users to select it in Settings
- Apply translations to all UI elements on page reload

## Adding New Translation Keys

When you add new UI text that needs translation:

### Step 1: Identify All Languages

Find the `translations.json` file and add your new key to every language:

```json
{
  "sr": {
    "new_feature": "Nova karakteristika",
    ...
  },
  "en": {
    "new_feature": "New Feature",
    ...
  }
}
```

### Step 2: Use in HTML/Templates

In your HTML templates, use `data-i18n` attributes:

```html
<button data-i18n="new_feature">Nova karakteristika</button>
<label data-i18n="new_feature">Nova karakteristika</label>

<!-- For input placeholders, use data-i18n-placeholder -->
<input type="text" data-i18n-placeholder="search_query" placeholder="...">
```

### Step 3: Use in JavaScript

In your JavaScript code, use the `t()` helper function:

```javascript
const message = t('new_feature');
alert(message);
```

### Step 4: Server Will Apply Translations

When the page loads:
1. JavaScript fetches translations from `/settings/public/config`
2. `initI18n()` function replaces all `data-i18n` attributes with translated text
3. `t()` helper can be used anywhere to get translations

## Architecture Overview

### Data Flow

```
User selects language in Settings
         ↓
Settings saved to database: database.setting["language"] = "en"
         ↓
User refreshes page / navigates
         ↓
Frontend calls /settings/public/config API
         ↓
Backend loads current language from database
         ↓
Backend returns translations for that language from translations.json
         ↓
Frontend receives translations in CONFIG object
         ↓
initI18n() replaces all data-i18n elements with translated text
         ↓
t() helper function now returns correct language for any key
```

### Files Involved

| File | Purpose | Language |
|------|---------|----------|
| `frontend/static/translations.json` | All translation strings | JSON |
| `app/utils/i18n.py` | Loads JSON and manages i18n | Python |
| `app/routes/settings.py` | `/settings/public/config` endpoint | Python |
| `frontend/static/app.js` | `t()` helper, `initI18n()` function | JavaScript |
| HTML templates | Use `data-i18n` attributes | HTML/Django |

## Example: Adding Spanish Support

### Edit `frontend/static/translations.json`:

Add this block after English:
```json
  "es": {
    "app_title": "Biblioteca — Sistema de Gestión",
    "dashboard": "Panel de Control",
    "books": "Libros",
    "members": "Miembros",
    "save": "Guardar",
    ... (add all other keys)
  }
```

### Update `frontend/templates/settings.html`:

```html
<select id="setting-language" class="form-control">
    <option value="sr">Srpski</option>
    <option value="en">English</option>
    <option value="es">Español</option>
</select>
```

### Test

1. Restart the application
2. Go to Settings → General
3. Select "Español" from Language dropdown
4. Click "Save"
5. All UI text should change to Spanish

## Translation Keys Reference

Here's a quick reference of common keys:

| Key | Purpose |
|-----|---------|
| `dashboard` | Main dashboard tab |
| `books` | Books management section |
| `members` | Members management section |
| `save` | Save button text |
| `delete` | Delete button text |
| `session_expired` | Session timeout message |
| `error` | Generic error message |

For a complete list, see `frontend/static/translations.json`.

## Notes

- Always include all languages when adding new keys
- If a key is missing, the application will display the key name itself (e.g., "missing_key")
- Case matters: `Dashboard` ≠ `dashboard`
- Use underscore for multi-word keys: `library_name`, not `libraryName`
- Restart the application after editing `translations.json` for changes to take effect
- The language is persisted in the database, so users' choice is remembered

## Quick Command: How to Add a Translation

1. **Tell me** which language/key you want to add
2. **I'll update** `frontend/static/translations.json` automatically
3. **I'll update** HTML templates if needed
4. **You'll test** by selecting the language in Settings

Example: "Dodaj prevod za 'Create new book' na srpskom: 'Kreiraj novu knjigu'"

I will:
- Add `"create_new_book": "Kreiraj novu knjigu"` to Serbian translations
- Add `"create_new_book": "Create new book"` to English translations
- Show you where to use it in HTML (`data-i18n="create_new_book"`)
