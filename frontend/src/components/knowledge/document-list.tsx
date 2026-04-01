'use client';

import React from 'react';
import { FileText, Calendar, Score } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useKnowledgeStore, SearchResult } from '@/lib/stores/knowledge-store';

interface DocumentListProps {
  onSelectDocument: (doc: SearchResult) => void;
}

export function DocumentList({ onSelectDocument }: DocumentListProps) {
  const { searchResults, filter } = useKnowledgeStore();

  const sortedResults = [...searchResults].sort((a, b) => {
    if (filter === 'relevance') {
      return (b.relevance_score || 0) - (a.relevance_score || 0);
    }
    return 0;
  });

  if (searchResults.length === 0) {
    return (
      <Card className="flex-1 min-h-[200px]">
        <CardContent className="flex flex-col items-center justify-center h-full py-12">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground text-center">
            No documents found. Try searching or upload a new document.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {sortedResults.map((doc) => (
        <Card
          key={doc.id}
          className="cursor-pointer hover:bg-accent/50 transition-colors"
          onClick={() => onSelectDocument(doc)}
        >
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <CardTitle className="text-base font-medium line-clamp-1">
                  {doc.title}
                </CardTitle>
              </div>
              {doc.relevance_score !== undefined && (
                <Badge variant="secondary" className="ml-2">
                  <Score className="h-3 w-3 mr-1" />
                  {(doc.relevance_score * 100).toFixed(0)}%
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
              {doc.content}
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                {doc.metadata?.file_name || 'Unknown file'}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
