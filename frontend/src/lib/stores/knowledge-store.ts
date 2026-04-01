import { create } from 'zustand';

export interface Document {
  id: string;
  title: string;
  content: string;
  file_path: string;
  file_name: string;
  created_at: string;
  relevance_score?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  metadata: {
    file_path: string;
    file_name: string;
  };
  relevance_score?: number;
}

interface KnowledgeState {
  documents: Document[];
  searchResults: SearchResult[];
  selectedDocument: Document | null;
  isLoading: boolean;
  isSearching: boolean;
  searchQuery: string;
  filter: 'date' | 'relevance';
  error: string | null;

  setDocuments: (documents: Document[]) => void;
  setSearchResults: (results: SearchResult[]) => void;
  setSelectedDocument: (document: Document | null) => void;
  setLoading: (loading: boolean) => void;
  setSearching: (searching: boolean) => void;
  setSearchQuery: (query: string) => void;
  setFilter: (filter: 'date' | 'relevance') => void;
  setError: (error: string | null) => void;
  clearSearchResults: () => void;
}

export const useKnowledgeStore = create<KnowledgeState>((set) => ({
  documents: [],
  searchResults: [],
  selectedDocument: null,
  isLoading: false,
  isSearching: false,
  searchQuery: '',
  filter: 'relevance',
  error: null,

  setDocuments: (documents) => set({ documents }),
  setSearchResults: (results) => set({ searchResults: results }),
  setSelectedDocument: (document) => set({ selectedDocument: document }),
  setLoading: (loading) => set({ isLoading: loading }),
  setSearching: (searching) => set({ isSearching: searching }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilter: (filter) => set({ filter }),
  setError: (error) => set({ error }),
  clearSearchResults: () => set({ searchResults: [] }),
}));
