package com.example.kbrag.service;

import org.springframework.ai.document.Document;
import org.springframework.ai.reader.markdown.MarkdownDocumentReader;
import org.springframework.ai.reader.markdown.config.MarkdownDocumentReaderConfig;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;

@Service
public class IngestService {

    private final VectorStore vectorStore;
    private final Path corpusDir;
    private final int chunkSize;
    private final int chunkOverlap;

    public IngestService(
            VectorStore vectorStore,
            @Value("${rag.corpus-dir}") String corpusDir,
            @Value("${rag.chunk-size}") int chunkSize,
            @Value("${rag.chunk-overlap}") int chunkOverlap) {
        this.vectorStore = vectorStore;
        this.corpusDir = Path.of(corpusDir).toAbsolutePath().normalize();
        this.chunkSize = chunkSize;
        this.chunkOverlap = chunkOverlap;
    }

    public int ingestCorpus() {
        List<Document> allChunks = new ArrayList<>();
        TokenTextSplitter splitter = new TokenTextSplitter(chunkSize, chunkOverlap, 5, 10000, true);

        try (Stream<Path> paths = Files.list(corpusDir)) {
            paths.filter(p -> p.toString().endsWith(".md"))
                    .filter(p -> !p.getFileName().toString().equals("MANIFEST.md"))
                    .sorted(Comparator.comparing(path -> path.getFileName().toString()))
                    .forEach(path -> allChunks.addAll(loadAndSplit(path, splitter)));
        } catch (IOException e) {
            throw new IllegalStateException("Failed to read corpus dir: " + corpusDir, e);
        }

        if (allChunks.isEmpty()) {
            throw new IllegalStateException("No markdown files found in " + corpusDir);
        }

        vectorStore.add(allChunks);
        return allChunks.size();
    }

    private List<Document> loadAndSplit(Path path, TokenTextSplitter splitter) {
        MarkdownDocumentReaderConfig config = MarkdownDocumentReaderConfig.builder()
                .withHorizontalRuleCreateDocument(true)
                .withIncludeCodeBlock(false)
                .withIncludeBlockquote(false)
                .build();
        MarkdownDocumentReader reader = new MarkdownDocumentReader(new FileSystemResource(path.toFile()), config);
        List<Document> docs = reader.get();
        docs.forEach(doc -> doc.getMetadata().put("source", path.getFileName().toString()));
        return splitter.apply(docs);
    }
}
