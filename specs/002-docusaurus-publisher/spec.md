# Feature Specification: AI-Driven Docusaurus Book Publisher

**Feature Branch**: `002-docusaurus-publisher`
**Created**: 2026-01-03
**Status**: Draft
**Input**: User description: "Feature: AI-Driven Docusaurus Book Creation and Publishing - Create a system that takes user-provided book content (markdown/text), formats it into a Docusaurus static site structure, deploys it to GitHub Pages via API, and automatically ingests the book into the RAG chatbot for querying."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Format Book Content to Docusaurus Structure (Priority: P1)

A content author provides book content as markdown files or structured text. The system analyzes the content structure, identifies chapters and sections, and generates a complete Docusaurus project with proper MDX files, navigation sidebars, and configuration. The author can review the generated structure locally before deployment.

**Why this priority**: This is the core transformation capability and foundation for all other features. Without proper formatting, deployment and ingestion cannot succeed. This delivers immediate value by automating the tedious task of converting raw content to Docusaurus format.

**Independent Test**: Provide sample markdown files, run the formatting command, verify that a valid Docusaurus project is created with correct file structure, sidebars navigation, and config. Can be tested locally without any deployment or GitHub integration.

**Acceptance Scenarios**:

1. **Given** a directory containing 10 markdown files with chapter headings, **When** the user runs the formatting command with a book title, **Then** the system creates a Docusaurus project with 10 MDX files, a sidebar configuration with proper ordering, and a docusaurus.config.js with the book title
2. **Given** markdown files with frontmatter metadata (title, order), **When** the formatting command processes them, **Then** the system respects the metadata for chapter ordering and titles in the sidebar
3. **Given** markdown content with code blocks, images, and links, **When** formatted to Docusaurus, **Then** all formatting is preserved and images are copied to the static assets directory
4. **Given** nested sections within chapters (using heading levels), **When** formatted, **Then** the sidebar shows proper hierarchical navigation
5. **Given** a single large text file with chapter markers, **When** formatted, **Then** the system splits it into multiple MDX files organized by chapter

---

### User Story 2 - Deploy Docusaurus Book to GitHub Pages (Priority: P2)

After formatting the book content, the user initiates deployment. The system creates a new GitHub repository under the user's account, pushes the Docusaurus project, sets up GitHub Actions for automated builds, and enables GitHub Pages. The user receives a live URL where the book is publicly accessible.

**Why this priority**: Deployment is the primary distribution mechanism, making the book accessible to readers. However, it depends on having properly formatted content (P1). This can be tested independently by deploying a sample book and verifying the live site.

**Independent Test**: Use a pre-formatted Docusaurus project, run the deployment command, verify that a new GitHub repository is created, GitHub Pages is enabled, and the book is accessible at the expected URL (https://username.github.io/book-slug/).

**Acceptance Scenarios**:

1. **Given** a formatted Docusaurus project and valid GitHub credentials, **When** the user runs the deploy command, **Then** a new repository is created with name matching the pattern "book-{slug}", the Docusaurus code is pushed, and GitHub Pages is enabled
2. **Given** a deployed book, **When** accessing the GitHub Pages URL, **Then** the Docusaurus site loads with proper navigation, all chapters are accessible, and styling is correct
3. **Given** deployment in progress, **When** querying deployment status, **Then** the system shows current stage (creating repo, pushing code, enabling Pages, building site) and estimated time remaining
4. **Given** a GitHub API error (rate limit, authentication failure), **When** deployment is attempted, **Then** the system provides a clear error message with troubleshooting guidance and does not leave partial repositories
5. **Given** a book with 50 chapters and images, **When** deployed, **Then** the complete deployment (repo creation, push, Pages enable, build) completes within 2 minutes

---

### User Story 3 - Auto-Ingest Book into RAG Chatbot (Priority: P3)

After a book is formatted (and optionally deployed), the system extracts the full text content, processes it through the existing ingestion pipeline (chunking, embedding, storage), and makes the book queryable via the RAG chatbot. Users can immediately ask questions about the book content.

**Why this priority**: Integration with the RAG chatbot completes the full-cycle workflow, enabling AI-powered book querying. This is valuable but not essential for the core book publishing feature. It depends on P1 (formatted content) but can work without P2 (deployment).

**Independent Test**: Use a formatted Docusaurus book (without deploying), run the ingestion command, verify that chunks appear in PostgreSQL and Qdrant, and confirm the RAG chatbot can answer questions about the book content.

**Acceptance Scenarios**:

1. **Given** a formatted Docusaurus book with 20 chapters, **When** the auto-ingestion command runs, **Then** the system extracts text from all MDX files, creates chunks following the 800-token / 128-overlap rule, and stores them in both PostgreSQL and Qdrant
2. **Given** a book with code examples and special formatting, **When** ingested, **Then** the system strips Docusaurus-specific syntax (import statements, JSX components) and preserves only readable text content
3. **Given** a successfully ingested book, **When** a user queries the RAG chatbot about a specific chapter topic, **Then** the chatbot retrieves relevant chunks and provides accurate answers with citations
4. **Given** a deployment that includes auto-ingestion, **When** GitHub Pages build completes, **Then** the ingestion process automatically triggers and completes within 1 minute
5. **Given** a book being re-ingested (updates), **When** ingestion runs, **Then** the system removes old chunks for that book_id and replaces them with new chunks to avoid duplicates

---

### Edge Cases

- What happens when markdown files have no clear chapter structure (flat list of topics)?
- How does the system handle very large books (100+ chapters, 500+ pages)?
- What if the GitHub repository name already exists under the user's account?
- How does the system handle books with non-Latin characters in titles or content?
- What if Docusaurus build fails due to invalid MDX syntax in user content?
- How does the system handle network interruptions during GitHub push operations?
- What if a book has duplicate chapter titles or conflicting metadata?
- How are images and media files handled if they're referenced with relative paths?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept book content in two formats: (a) directory of markdown files, or (b) structured text with chapter markers
- **FR-002**: System MUST analyze content structure to identify chapters, sections, and hierarchy based on markdown heading levels (# = chapter, ## = section)
- **FR-003**: System MUST generate valid Docusaurus v3.x project structure including docs/ directory, sidebars.js, docusaurus.config.js, package.json, and static/ assets
- **FR-004**: System MUST convert markdown to MDX format while preserving code blocks, tables, lists, images, and links
- **FR-005**: System MUST generate a sidebar navigation file (sidebars.js) with chapters ordered by filename sorting or explicit frontmatter "order" metadata
- **FR-006**: System MUST create a docusaurus.config.js with book title, author (GitHub username), and GitHub Pages deployment configuration
- **FR-007**: System MUST use GitHub API to create a new public repository with name pattern {GITHUB_REPO_PREFIX}{book-slug} where slug is derived from the book title
- **FR-008**: System MUST push Docusaurus project to the created GitHub repository including all files, commits, and preserve Git history
- **FR-009**: System MUST enable GitHub Pages for the repository via API, configured to deploy from the gh-pages branch
- **FR-010**: System MUST create a GitHub Actions workflow file (.github/workflows/deploy.yml) that builds and deploys Docusaurus on push to main branch
- **FR-011**: System MUST extract plain text from all MDX files, removing Docusaurus-specific syntax (imports, JSX components, frontmatter) for RAG ingestion
- **FR-012**: System MUST ingest extracted text using the existing RAG pipeline (backend/src/services/ingestion.py) with standard chunking parameters (800 tokens, 128 overlap)
- **FR-013**: System MUST provide a CLI tool (backend/src/cli/create_book.py) accepting arguments: --content-dir, --title, --author, --deploy (optional), --ingest (optional)
- **FR-014**: System MUST provide an API endpoint (POST /api/v1/books/create) accepting JSON with content_files, title, metadata, and deployment options
- **FR-015**: System MUST track and report deployment status with stages: formatting (10%), creating repo (20%), pushing code (40%), enabling Pages (60%), building site (80%), complete (100%)
- **FR-016**: System MUST handle GitHub API errors (authentication failures, rate limits, network timeouts) with clear error messages and automatic retry logic (max 3 retries with exponential backoff)
- **FR-017**: System MUST validate GitHub token permissions before deployment and fail fast if token lacks repo creation or Pages administration rights
- **FR-018**: System MUST check for repository name conflicts and either (a) fail with clear message, or (b) append numeric suffix (-2, -3) to resolve conflict
- **FR-019**: System MUST copy referenced images and media files to Docusaurus static/ directory and update MDX references to use correct paths
- **FR-020**: System MUST generate a default landing page (docs/intro.md) if no introduction file is provided

### Key Entities *(include if feature involves data)*

- **Book**: Represents the complete book project with title, author, slug, creation timestamp, deployment URL, GitHub repository URL, ingestion status
- **Chapter**: Individual content unit within a book with title, order/position, MDX content, word count, associated images/assets
- **DocusaurusProject**: Generated project structure with configuration (docusaurus.config.js), navigation (sidebars.js), content files (docs/), and build artifacts
- **DeploymentJob**: Tracks deployment progress with stages (formatting, repo_creation, code_push, pages_enable, site_build), status (pending/in_progress/completed/failed), and timestamps
- **GitHubRepository**: External GitHub repo with name, URL, Pages URL, creation timestamp, and last sync time

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can format a 20-chapter book into a complete Docusaurus project in under 30 seconds
- **SC-002**: Complete end-to-end deployment (format + GitHub + Pages) completes within 2 minutes for books up to 50 chapters
- **SC-003**: Deployed books render correctly on GitHub Pages with functional navigation, proper styling, and all assets loaded
- **SC-004**: RAG chatbot can answer questions about ingested books with 90%+ accuracy (based on citation relevance)
- **SC-005**: CLI tool successfully completes full workflow (format + deploy + ingest) with a single command
- **SC-006**: API endpoint returns deployment progress updates every 5 seconds with accurate status percentages
- **SC-007**: System handles 95% of GitHub API errors gracefully without leaving orphaned repositories or partial state
- **SC-008**: Books with 5-50 chapters are fully supported; books outside this range show clear warnings about potential issues
- **SC-009**: Deployed book URLs follow predictable pattern (https://{username}.github.io/{book-slug}/) and are accessible within 60 seconds of deployment completion
- **SC-010**: 100% of markdown syntax (code blocks, tables, lists, links, images) is preserved in the deployed Docusaurus site

## Constraints & Assumptions

### Technical Constraints

- Requires Node.js 18+ installed on the system for Docusaurus builds
- Requires valid GitHub personal access token with `repo` and `workflow` scopes
- GitHub API rate limit: 5000 requests/hour (authenticated); system must stay well below this limit
- Docusaurus version locked to 3.x for stability and compatibility
- Maximum book size: 50 chapters / 200,000 words (to ensure performance)
- Repository visibility: All created repositories are public (private repo support requires paid GitHub account)

### Assumptions

- Users provide content in valid markdown format with consistent heading structure
- Users have GitHub accounts and can generate personal access tokens
- Network connectivity is available for GitHub API calls and git operations
- Docusaurus builds succeed if content is valid markdown (no custom React components)
- Book titles are unique per user (no two books with identical titles)
- Images referenced in markdown exist in the content directory or are accessible URLs
- Users understand basic Git and GitHub concepts for troubleshooting deployment issues

### Security Considerations

- GitHub tokens must be stored securely in environment variables, never in code or logs
- Tokens should have minimal required permissions (repo creation, Pages administration only)
- System must validate and sanitize user-provided content to prevent code injection in generated files
- Repository names must be validated to prevent special characters that could cause security issues
- Deployment logs must not expose sensitive information (tokens, API keys, credentials)

## Dependencies

### External Dependencies

- **GitHub API v3**: Required for repository creation, content push, and Pages configuration
- **Docusaurus v3.x**: Core static site generator framework
- **Node.js & npm**: Required for building Docusaurus projects
- **Git CLI**: Required for repository operations (clone, commit, push)
- **Existing RAG System**: Depends on backend/src/services/ingestion.py for book text ingestion

### Internal Dependencies

- Must integrate with existing RAG chatbot ingestion pipeline (Phase 2 foundational tasks)
- Uses existing PostgreSQL and Qdrant databases for chunk storage
- Requires existing OpenAI API integration for embeddings generation
- CLI tool follows existing patterns from backend/src/cli/ingest.py

## Out of Scope

- AI-powered content generation (users must provide content; system only formats)
- Support for platforms other than GitHub Pages (no Netlify, Vercel, etc.)
- Custom Docusaurus themes or plugins (uses default theme)
- Collaborative editing or version control for book content (users manage via Git)
- Analytics or reader engagement tracking for deployed books
- PDF or ePub export from Docusaurus sites
- Automated spell-checking or grammar correction
- Multi-language book support (internationalization)
- Private repository deployments (requires paid GitHub accounts)
