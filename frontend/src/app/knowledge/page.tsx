'use client';

import React, { useState, useCallback } from 'react';
import { Plus, Library } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SearchBar } from '@/components/knowledge/search-bar';
import { DocumentList } from '@/components/knowledge/document-list';
import { DocumentViewer } from '@/components/knowledge/document-viewer';
import { UploadForm } from '@/components/knowledge/upload-form';
import { useKnowledgeStore, SearchResult, Document } from '@/lib/stores/knowledge-store';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export default function KnowledgePage() {
  const {
    searchResults,
    setSearchResults,
    isSearching,
    setSearching,
    selectedDocument,
    setSelectedDocument,
    setError,
  } = useKnowledgeStore();

  const [activeTab, setActiveTab] = useState('search');

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/knowledge/search?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, [API_BASE, setSearchResults, setSearching, setError]);

  const handleUpload = useCallback(async (files: FileList) => {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${API_BASE}/load_file`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Upload successful:', data);

    // Switch to search tab after upload
    setActiveTab('search');
  }, [API_BASE]);

  const handleSelectDocument = useCallback((doc: SearchResult) => {
    // Convert SearchResult to Document format
    const document: Document = {
      id: doc.id,
      title: doc.title,
      content: doc.content,
      file_path: doc.metadata.file_path,
      file_name: doc.metadata.file_name,
      created_at: '', // Search results don't have created_at
      relevance_score: doc.relevance_score,
    };
    setSelectedDocument(document);
  }, [setSelectedDocument]);

  const handleCloseDocument = useCallback(() => {
    setSelectedDocument(null);
  }, [setSelectedDocument]);

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Library className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Knowledge Base</h1>
            <p className="text-sm text-muted-foreground">
              Search and manage your indexed documents
            </p>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="upload">Upload</TabsTrigger>
        </TabsList>

        <TabsContent value="search" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <SearchBar onSearch={handleSearch} />
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-4">
              {isSearching ? (
                <Card className="flex-1 min-h-[200px]">
                  <CardContent className="flex flex-col items-center justify-center h-full py-12">
                    <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    <p className="text-muted-foreground mt-4">Searching...</p>
                  </CardContent>
                </Card>
              ) : (
                <DocumentList onSelectDocument={handleSelectDocument} />
              )}
            </div>

            <DocumentViewer
              document={selectedDocument}
              onClose={handleCloseDocument}
            />
          </div>
        </TabsContent>

        <TabsContent value="upload">
          <div className="max-w-xl">
            <UploadForm onUpload={handleUpload} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
