import {
  FiActivity,
  FiBox,
  FiCheckCircle,
  FiClock,
  FiCode,
  FiCommand,
  FiCpu,
  FiDatabase,
  FiFileText,
  FiGitBranch,
  FiGlobe,
  FiKey,
  FiLayers,
  FiMessageSquare,
  FiSearch,
  FiServer,
  FiShield,
  FiTerminal,
  FiUploadCloud,
  FiZap,
} from 'react-icons/fi'

export const navItems = [
  { label: 'Home', href: '/' },
  { label: 'Documentation', href: '/documentation' },
  { label: 'API Reference', href: '/api-reference' },
  { label: 'SDK', href: '/sdk' },
  { label: 'Tutorials', href: '/tutorials' },
  { label: 'Guides', href: '/guides' },
  { label: 'FAQ', href: '/faq' },
]

export const docCards = [
  { title: 'Authentication', icon: FiKey, description: 'Learn API keys, OAuth flows, scopes, session renewal, and secure token storage.' },
  { title: 'REST APIs', icon: FiServer, description: 'Explore endpoints, request formats, pagination, filtering, and production response contracts.' },
  { title: 'SDK Installation', icon: FiBox, description: 'Install JavaScript, Python, and server SDKs with environment-specific setup guidance.' },
  { title: 'Quick Start', icon: FiZap, description: 'Launch your first documentation-aware AI workflow in a few focused steps.' },
  { title: 'Webhooks', icon: FiGitBranch, description: 'Subscribe to events, verify signatures, and replay deliveries without losing state.' },
  { title: 'Error Handling', icon: FiShield, description: 'Decode error classes, retry policies, rate responses, and recovery suggestions.' },
  { title: 'Rate Limits', icon: FiClock, description: 'Understand quota windows, burst control, headers, and resilient client behavior.' },
  { title: 'Examples', icon: FiCode, description: 'Copy polished implementation examples for search, upload, chat, and source display.' },
  { title: 'GraphQL', icon: FiDatabase, description: 'Query typed schemas, fragments, mutations, and documentation entities efficiently.' },
  { title: 'CLI', icon: FiTerminal, description: 'Automate indexing, local previews, PDF ingestion, and deployment checks from terminal.' },
]

export const featureCards = [
  { title: 'Website Knowledge Search', icon: FiGlobe, description: 'Search docs, guides, references, and release notes from one intelligent surface.' },
  { title: 'Semantic Search', icon: FiSearch, description: 'Find intent-matched answers even when users phrase questions differently.' },
  { title: 'Hybrid Search', icon: FiLayers, description: 'Combine keyword precision with vector recall for dependable developer answers.' },
  { title: 'PDF Question Answering', icon: FiUploadCloud, description: 'Upload technical PDFs and ask direct questions against their contents.' },
  { title: 'Source Attribution', icon: FiFileText, description: 'Show whether every answer came from the website, uploaded PDFs, or both.' },
  { title: 'Conversation Memory', icon: FiMessageSquare, description: 'Keep follow-up questions grounded in previous context and user intent.' },
  { title: 'Fast AI Responses', icon: FiActivity, description: 'Responsive interface states make streaming-ready AI conversations feel immediate.' },
  { title: 'Groq Ready', icon: FiCpu, description: 'Prepared frontend service boundaries for high-speed Groq-backed responses.' },
  { title: 'Gemini Ready', icon: FiCheckCircle, description: 'Model-agnostic request helpers make future Gemini integration straightforward.' },
  { title: 'Developer Friendly', icon: FiCommand, description: 'Keyboard shortcuts, readable code blocks, copy tools, and exportable sessions.' },
]

export const suggestedQuestions = [
  'How do I authenticate?',
  'Show API examples',
  'Explain Rate Limits',
  'Upload a PDF',
  'Quick Start Guide',
  'How do SDKs work?',
]

export const recentChats = [
  'Auth headers and scopes',
  'PDF upload workflow',
  'Webhook retry policy',
]

export const tutorials = [
  { title: 'Build a RAG-powered search box', level: 'Intermediate', time: '18 min', description: 'Connect documentation search, relevance signals, and answer summaries into one flow.' },
  { title: 'Ship PDF question answering', level: 'Advanced', time: '24 min', description: 'Design an upload UI that later plugs into a document parsing and retrieval pipeline.' },
  { title: 'Create a source-aware chat panel', level: 'Beginner', time: '12 min', description: 'Display messages, citations, chips, empty states, and helpful response actions.' },
]

export const faqItems = [
  { question: 'Does this frontend include a backend?', answer: 'No. It only prepares clean API methods and interface states for a future FastAPI or Flask backend.' },
  { question: 'Can I connect real AI models later?', answer: 'Yes. The service layer is model-agnostic and can send chat, history, clear, and PDF upload requests to your backend.' },
  { question: 'Is PDF upload functional?', answer: 'The UI validates PDF files and shows progress/success states. Real storage and parsing belong in the future backend.' },
  { question: 'Does the chat support source attribution?', answer: 'Yes. Assistant messages render website, PDF, or combined source badges below the answer.' },
]

export const apiRows = [
  { method: 'POST', path: '/chat', description: 'Send a user question and optional session metadata to the assistant backend.' },
  { method: 'POST', path: '/upload-pdf', description: 'Upload a PDF document for future retrieval augmented generation.' },
  { method: 'GET', path: '/history', description: 'Load previous chat sessions and message history for the active user.' },
  { method: 'DELETE', path: '/history', description: 'Clear stored conversation history for a fresh assistant session.' },
]
