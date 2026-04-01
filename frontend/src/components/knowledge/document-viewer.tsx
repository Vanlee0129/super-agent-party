'use client';

import React from 'react';
import { X, FileText, Calendar, Link } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Document, SearchResult } from '@/lib/stores/knowledge-store';

type DocumentLike = Document | SearchResult;

interface DocumentViewerProps {
  document: DocumentLike | null;
  onClose: () => void;
}

export function DocumentViewer({ document, onClose }: DocumentViewerProps) {
  if (!document) {
    return (
      <Card className="flex-1 min-h-[200px]">
        <CardContent className="flex flex-col items-center justify-center h-full py-12">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground text-center">
            Select a document to view its content
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex-1 flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="h-5 w-5 text-primary flex-shrink-0" />
            <CardTitle className="text-lg truncate">{document.title}</CardTitle>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          {document.relevance_score !== undefined && (
            <Badge variant="secondary">
              Relevance: {(document.relevance_score * 100).toFixed(0)}%
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link className="h-4 w-4" />
            <span className="truncate" title={'file_path' in document ? document.file_path : document.metadata?.file_path}>
              {'file_path' in document ? document.file_path : document.metadata?.file_path || 'Unknown path'}
            </span>
          </div>

          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-2">Content</h3>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {document.content}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
