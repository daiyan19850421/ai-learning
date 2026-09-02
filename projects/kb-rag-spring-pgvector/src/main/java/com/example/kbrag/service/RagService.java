package com.example.kbrag.service;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RagService {

    private final ChatClient chatClient;
    private final VectorStore vectorStore;
    private final int topK;

    public RagService(ChatClient.Builder chatClientBuilder, VectorStore vectorStore, @Value("${rag.top-k}") int topK) {
        this.vectorStore = vectorStore;
        this.topK = topK;
        var searchRequest = SearchRequest.builder().topK(topK).build();
        this.chatClient = chatClientBuilder
                .defaultAdvisors(QuestionAnswerAdvisor.builder(vectorStore).searchRequest(searchRequest).build())
                .build();
    }

    public ChatResponse chat(String question) {
        String answer = chatClient.prompt()
                .user(question)
                .call()
                .content();

        List<Source> sources = vectorStore.similaritySearch(
                        SearchRequest.builder().query(question).topK(topK).build())
                .stream()
                .map(this::toSource)
                .toList();

        return new ChatResponse(question, answer, sources);
    }

    private Source toSource(Document doc) {
        String source = doc.getMetadata().getOrDefault("source", "unknown").toString();
        String excerpt = doc.getText();
        if (excerpt.length() > 280) {
            excerpt = excerpt.substring(0, 280) + "...";
        }
        return new Source(source, excerpt);
    }

    public record ChatRequest(String question) {
    }

    public record Source(String file, String excerpt) {
    }

    public record ChatResponse(String question, String answer, List<Source> sources) {
    }
}
