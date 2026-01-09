"""Docusaurus project builder service."""

import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from backend.src.core.logging import get_logger

logger = get_logger(__name__)


def sanitize_repo_name(title: str) -> str:
    """Convert title to valid GitHub repo name.

    Args:
        title: Book title

    Returns:
        Sanitized repo name (lowercase, hyphens, no special chars)
    """
    # Convert to lowercase and replace spaces with hyphens
    name = title.lower().replace(" ", "-")
    # Remove special characters, keep only alphanumeric and hyphens
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Remove consecutive hyphens
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    return name


def parse_chapters(content: str) -> list[dict[str, Any]]:
    """Parse content into chapters based on H1 headers.

    Args:
        content: Full markdown content

    Returns:
        List of chapter dicts with title and content
    """
    chapters = []

    # Split by H1 headers (# Title)
    parts = re.split(r'^# (.+)$', content, flags=re.MULTILINE)

    # First part is intro (before any H1)
    if parts[0].strip():
        chapters.append({
            "id": "intro",
            "title": "Introduction",
            "content": parts[0].strip()
        })

    # Process remaining parts (title, content pairs)
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            title = parts[i].strip()
            content = parts[i + 1].strip()

            # Create sanitized ID from title
            chapter_id = sanitize_repo_name(title)

            chapters.append({
                "id": chapter_id,
                "title": title,
                "content": content
            })

    logger.info(f"Parsed {len(chapters)} chapters from content")
    return chapters


def create_docusaurus_structure(
    output_dir: Path,
    title: str,
    content: str,
    author: str = "Anonymous",
    github_username: str = "",
    repo_name: str = ""
) -> None:
    """Create complete Docusaurus project structure.

    Args:
        output_dir: Directory to create project in
        title: Book title
        content: Full markdown content
        author: Book author
        github_username: GitHub username for deployment
        repo_name: Repository name
    """
    logger.info(f"Creating Docusaurus structure in {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse chapters
    chapters = parse_chapters(content)

    # Create docs directory
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(exist_ok=True)

    # Write chapter files
    for idx, chapter in enumerate(chapters, 1):
        file_name = f"{chapter['id']}.md"
        file_path = docs_dir / file_name

        # Add frontmatter
        frontmatter = f"""---
sidebar_position: {idx}
---

"""
        file_content = frontmatter + f"# {chapter['title']}\n\n{chapter['content']}"
        file_path.write_text(file_content, encoding="utf-8")
        logger.info(f"Created {file_name}")

    # Create package.json
    package_json = {
        "name": repo_name or sanitize_repo_name(title),
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "docusaurus": "docusaurus",
            "start": "docusaurus start",
            "build": "docusaurus build",
            "swizzle": "docusaurus swizzle",
            "deploy": "docusaurus deploy",
            "clear": "docusaurus clear",
            "serve": "docusaurus serve",
            "write-translations": "docusaurus write-translations",
            "write-heading-ids": "docusaurus write-heading-ids"
        },
        "dependencies": {
            "@docusaurus/core": "^3.5.2",
            "@docusaurus/preset-classic": "^3.5.2",
            "clsx": "^2.0.0",
            "prism-react-renderer": "^2.3.0",
            "react": "^18.0.0",
            "react-dom": "^18.0.0"
        },
        "engines": {
            "node": ">=20.0"
        }
    }
    (output_dir / "package.json").write_text(json.dumps(package_json, indent=2), encoding="utf-8")

    # Create docusaurus.config.js
    config_js = f"""const config = {{
  title: '{title}',
  tagline: 'by {author}',
  favicon: 'img/favicon.ico',
  url: 'https://{github_username}.github.io',
  baseUrl: '/{repo_name}/',
  organizationName: '{github_username}',
  projectName: '{repo_name}',
  onBrokenLinks: 'ignore',
  onBrokenMarkdownLinks: 'ignore',
  i18n: {{
    defaultLocale: 'en',
    locales: ['en'],
  }},
  presets: [
    [
      'classic',
      ({{
        docs: {{
          sidebarPath: './sidebars.js',
          routeBasePath: '/',
        }},
        blog: false,
        theme: {{}},
      }}),
    ],
  ],
  themeConfig: ({{
    navbar: {{
      title: '{title}',
      items: [
        {{
          href: 'https://github.com/{github_username}/{repo_name}',
          label: 'GitHub',
          position: 'right',
        }},
      ],
    }},
    footer: {{
      style: 'dark',
      copyright: `{title} - Built with Docusaurus`,
    }},
    prism: {{
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
    }},
  }}),
}};

module.exports = config;
"""
    (output_dir / "docusaurus.config.js").write_text(config_js, encoding="utf-8")

    # Create sidebars.js
    sidebar_items = [f"'{chapter['id']}'" for chapter in chapters]
    sidebars_js = f"""module.exports = {{
  courseSidebar: [
    {', '.join(sidebar_items)}
  ],
}};
"""
    (output_dir / "sidebars.js").write_text(sidebars_js, encoding="utf-8")

    # Create static directory and homepage redirect
    static_dir = output_dir / "static"
    static_dir.mkdir(exist_ok=True)

    first_chapter = chapters[0]["id"] if chapters else "intro"
    index_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0; URL=/{repo_name}/{first_chapter}">
    <link rel="canonical" href="/{repo_name}/{first_chapter}">
</head>
<body>
    <p>Redirecting to <a href="/{repo_name}/{first_chapter}">{title}</a>...</p>
    <script>
        window.location.href = '/{repo_name}/{first_chapter}';
    </script>
</body>
</html>
"""
    (static_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Create .gitignore
    gitignore = """.docusaurus
build
node_modules
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local
npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""
    (output_dir / ".gitignore").write_text(gitignore, encoding="utf-8")

    # Create GitHub Actions workflow
    github_dir = output_dir / ".github" / "workflows"
    github_dir.mkdir(parents=True, exist_ok=True)

    workflow = f"""name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Build website
        run: npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{{{ secrets.GITHUB_TOKEN }}}}
          publish_dir: ./build
          user_name: github-actions[bot]
          user_email: github-actions[bot]@users.noreply.github.com
"""
    (github_dir / "deploy.yml").write_text(workflow, encoding="utf-8")

    # Create README
    readme = f"""# {title}

by {author}

This book was automatically generated and deployed using the Docusaurus Book Creation System.

## Live Site

Visit the live site at: https://{github_username}.github.io/{repo_name}/

## Development

```bash
npm install
npm start
```

## Deployment

Pushes to the `main` branch automatically deploy to GitHub Pages via GitHub Actions.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    logger.info(f"Created complete Docusaurus structure with {len(chapters)} chapters")
