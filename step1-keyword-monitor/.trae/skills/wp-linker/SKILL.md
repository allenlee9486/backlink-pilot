---
name: "wp-linker"
description: "Automatically posts backlinks to WordPress blogs. Invoke when user provides a list of blog URLs to promote a website via comments."
---

# WP Linker Skill

This skill automates the process of posting comments with backlinks to a list of target WordPress (WP) and Blogger URLs.

## Functionality

- **Smart Commenting**: Uses AI to read the article title and generate a relevant, human-like comment.
- **Backlink Injection**: Injects a specific anchor text with a hyperlink (e.g., `<a href="https://buildaringfarm.xyz/">buildaringfarm</a>`) into the comment body.
- **Automated Form Filling**: Automatically fills in Name, Email, Website, and Comment fields on standard WP forms.
- **Session Reuse**: Connects to a local Chrome instance (port 9222) to reuse existing Google/Social logins.
- **Deduplication**: Ensures the same domain is not commented on multiple times using a local history file.
- **Anti-Spam**: Includes random delays between posts to mimic human behavior.

## When to Invoke

Invoke this skill when:
- The user provides a list of blog URLs for backlink building.
- The user wants to promote a website through automated blog comments.
- The user asks to "run the backlink tool" or "post links to these blogs".

## Usage

1. **Prerequisites**:
   - Chrome must be running with `--remote-debugging-port=9222`.
   - The user should be logged into their Google account in the debugging Chrome instance if login is required.

2. **Configuration**:
   - The target URLs and user info are managed within `monitors/wp_linker.py`.
   - History is stored in `monitors/data/wp_linker_history.json`.

3. **Execution**:
   Run the following command to start the process:
   ```bash
   python monitors/wp_linker.py
   ```

## Key Files

- [wp_linker.py](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/monitors/wp_linker.py): The main execution script.
- [wp_linker_history.json](file:///d%3A/%E5%BC%80%E5%8F%91%E8%AE%BE%E8%AE%A1%E5%B7%A5%E5%85%B7/jiankong_sitemap/monitors/data/wp_linker_history.json): Persistence layer for deduplication.
