package com.example.kbrag.controller;

import com.example.kbrag.service.IngestService;
import com.example.kbrag.service.RagService;
import com.example.kbrag.service.RagService.ChatRequest;
import com.example.kbrag.service.RagService.ChatResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class RagController {

    private final IngestService ingestService;
    private final RagService ragService;

    public RagController(IngestService ingestService, RagService ragService) {
        this.ingestService = ingestService;
        this.ragService = ragService;
    }

    @PostMapping("/ingest")
    public ResponseEntity<Map<String, Object>> ingest() {
        int chunks = ingestService.ingestCorpus();
        return ResponseEntity.ok(Map.of(
                "status", "ok",
                "chunks", chunks
        ));
    }

    @PostMapping("/chat")
    public ChatResponse chat(@RequestBody ChatRequest request) {
        return ragService.chat(request.question());
    }
}
