package com.musaib.resumeanalyzer.service;

import com.musaib.resumeanalyzer.entity.Resume;
import com.musaib.resumeanalyzer.repository.ResumeRepository;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class ResumeService {

    private static final String UPLOAD_DIR = System.getProperty("user.dir") + "/uploads";

    @org.springframework.beans.factory.annotation.Value("${ai.service.url}")
    private String aiServiceUrl;

    @org.springframework.beans.factory.annotation.Value("${ai.service.key}")
    private String aiServiceKey;

    @Autowired
    private ResumeRepository resumeRepository;

    @Autowired
    private RestTemplate restTemplate;

    // ── Get All Resumes ──────────────────────────────────────────────────────
    public List<Resume> getAllResumes() {
        return resumeRepository.findAll();
    }

    // ── Get Resume By ID ─────────────────────────────────────────────────────
    public Resume getResumeById(Long id) {
        if (id == null)
            return null;
        return resumeRepository.findById(id).orElse(null);
    }

    // ── Pure Analysis (No DB save, with cleanup) ─────────────────────────────
    public Map<String, Object> analyzeFile(MultipartFile file) throws IOException {
        Path uploadPath = Paths.get(UPLOAD_DIR);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }
        String safeFileName = UUID.randomUUID() + ".pdf";
        Path filePath = uploadPath.resolve(safeFileName);

        try {
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
            byte[] fileBytes = Files.readAllBytes(filePath);
            return callAiService("/analyze", safeFileName, fileBytes, null);
        } finally {
            Files.deleteIfExists(filePath);
        }
    }

    // ── Upload and Analyze (saves once) ──────────────────────────────────────
    public Map<String, Object> uploadAndAnalyze(MultipartFile file) throws IOException {
        // Save file persistently for DB record
        String safeFileName = UUID.randomUUID() + ".pdf";
        Path uploadPath = Paths.get(UPLOAD_DIR);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }
        System.out.println(">>> ResumeService: Starting upload and analyze for " + file.getOriginalFilename());
        Path filePath = uploadPath.resolve(safeFileName);
        Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
        System.out.println(">>> ResumeService: File saved at " + filePath);

        try {
            byte[] fileBytes = Files.readAllBytes(filePath);
            System.out.println(">>> ResumeService: Calling callAiService...");
            Map<String, Object> analysis = callAiService("/analyze", safeFileName, fileBytes, null);
            System.out.println(">>> ResumeService: Analysis result received: " + (analysis != null ? "YES" : "NO"));

            // Persist full analysis in DB
            Resume resume = new Resume();
            resume.setFileName(file.getOriginalFilename());
            resume.setFilePath(filePath.toString());
            resume.setUploadedAt(LocalDateTime.now());

            if (analysis != null) {
                if (analysis.get("score") instanceof Number scoreNum) {
                    resume.setAtsScore(scoreNum.intValue());
                }
                if (analysis.get("strengths") instanceof List<?> list) {
                    resume.setStrengths(list.stream().map(Object::toString).toList());
                }
                Object missing = analysis.getOrDefault("missing_keywords", analysis.get("missingKeywords"));
                if (missing instanceof List<?> list) {
                    resume.setMissingKeywords(list.stream().map(Object::toString).toList());
                }
                if (analysis.get("suggestions") instanceof List<?> list) {
                    resume.setSuggestions(list.stream().map(Object::toString).toList());
                }
                if (analysis.get("career_recommendations") instanceof List<?> list) {
                    resume.setCareerRecommendations(list.stream().map(Object::toString).toList());
                }
            }
            resumeRepository.save(resume);
            return analysis;
        } catch (Exception e) {
            throw e;
        }
    }

    // ── Delete Resume (with file cleanup) ────────────────────────────────────
    public void deleteResume(Long id) throws IOException {
        if (id == null)
            return;
        Resume resume = resumeRepository.findById(id).orElse(null);
        if (resume != null) {
            if (resume.getFilePath() != null) {
                Files.deleteIfExists(Paths.get(resume.getFilePath()));
            }
            resumeRepository.delete(resume);
        }
    }

    // ── Scheduled Cleanup: Remove files/records older than 30 days ────────────
    @org.springframework.scheduling.annotation.Scheduled(cron = "0 0 2 * * ?") // Every day at 2 AM
    public void cleanupOldResumes() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(30);
        java.util.List<Resume> oldResumes = resumeRepository.findAll().stream()
                .filter(r -> r.getUploadedAt().isBefore(cutoff))
                .toList();

        for (Resume r : oldResumes) {
            try {
                deleteResume(r.getId());
                System.out.println(">>> Cleanup: Deleted old resume " + r.getId());
            } catch (IOException e) {
                System.err.println(">>> Cleanup Error: " + e.getMessage());
            }
        }
    }

    // ── Match Resume with Job Description (with cleanup) ─────────────────────
    public Map<String, Object> matchJob(MultipartFile file, String jobDescription) throws IOException {
        Path uploadPath = Paths.get(UPLOAD_DIR);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }
        String safeFileName = UUID.randomUUID() + ".pdf";
        Path filePath = uploadPath.resolve(safeFileName);

        try {
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
            byte[] fileBytes = Files.readAllBytes(filePath);
            return callAiService("/match", safeFileName, fileBytes, jobDescription);
        } finally {
            Files.deleteIfExists(filePath);
        }
    }

    // ── Optimize Resume (suggest rewrites) ──────────────────────────────────
    public Map<String, Object> optimizeResume(MultipartFile file) throws IOException {
        Path uploadPath = Paths.get(UPLOAD_DIR);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }
        String safeFileName = UUID.randomUUID() + ".pdf";
        Path filePath = uploadPath.resolve(safeFileName);

        try {
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
            byte[] fileBytes = Files.readAllBytes(filePath);
            return callAiService("/optimize", safeFileName, fileBytes, null);
        } finally {
            Files.deleteIfExists(filePath);
        }
    }

    public Map<String, Object> generateInterviewQuestions(MultipartFile file) throws IOException {
        Path uploadPath = Paths.get(UPLOAD_DIR);
        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }
        String safeFileName = UUID.randomUUID() + ".pdf";
        Path filePath = uploadPath.resolve(safeFileName);

        try {
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
            byte[] fileBytes = Files.readAllBytes(filePath);
            return callAiService("/interview-prep", safeFileName, fileBytes, null);
        } finally {
            Files.deleteIfExists(filePath);
        }
    }

    // ── Generate PDF Report (uses analyzeFile to avoid double save) ──────────
    public byte[] generatePdfReport(MultipartFile file) throws Exception {
        Map<String, Object> analysis = analyzeFile(file);
        Map<String, Object> optimizations = optimizeResume(file);

        try (PDDocument document = new PDDocument();
                ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {

            PDPage page = new PDPage();
            document.addPage(page);

            PDType1Font bold = new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD);
            PDType1Font regular = new PDType1Font(Standard14Fonts.FontName.HELVETICA);
            PDType1Font italic = new PDType1Font(Standard14Fonts.FontName.HELVETICA_OBLIQUE);

            try (PDPageContentStream cs = new PDPageContentStream(document, page)) {
                float y = 780;
                float margin = 60;
                float pageWidth = page.getMediaBox().getWidth();

                // ── 1. Header with Branding ──────────────────────────────────────────
                cs.setNonStrokingColor(new Color(99, 102, 241)); // Indigo theme
                cs.addRect(0, 750, pageWidth, 50);
                cs.fill();

                cs.setNonStrokingColor(Color.WHITE);
                cs.beginText();
                cs.setFont(bold, 18);
                cs.newLineAtOffset(margin, 765);
                cs.showText("AI RESUME ANALYSIS REPORT");
                cs.endText();
                y = 730;

                // ── 2. Summary Dashboard ─────────────────────────────────────────────
                cs.setNonStrokingColor(Color.BLACK);
                y = writeLine(cs, bold, 12, margin, y, "ANALYSIS SUMMARY");

                int score = (analysis.get("score") instanceof Number n) ? n.intValue() : 0;
                y = writeLine(cs, regular, 11, margin, y, "ATS Compatibility Score: " + score + "/100");

                // Draw Score Bar
                cs.setNonStrokingColor(new Color(226, 232, 240));
                cs.addRect(margin, y - 5, 200, 10);
                cs.fill();
                cs.setNonStrokingColor(new Color(16, 185, 129)); // Success Emerald
                cs.addRect(margin, y - 5, (200 * score / 100f), 10);
                cs.fill();
                y -= 25;

                y = writeLine(cs, regular, 10, margin, y, "Word Count: " + analysis.get("word_count"));
                y -= 15;

                // ── 3. Key Strengths ─────────────────────────────────────────────────
                drawDivider(cs, margin, y, pageWidth - 2 * margin);
                y -= 20;
                y = writeLine(cs, bold, 11, margin, y, "KEY STRENGTHS");
                if (analysis.get("strengths") instanceof List<?> list) {
                    for (Object item : list) {
                        y = writeLine(cs, regular, 10, margin + 10, y, "•  " + item);
                    }
                }
                y -= 10;

                // ── 4. Smart Optimizations (Professional Rewrites) ──────────────────
                drawDivider(cs, margin, y, pageWidth - 2 * margin);
                y -= 20;
                y = writeLine(cs, bold, 11, margin, y, "AI SMART OPTIMIZATIONS (REWRITES)");
                if (optimizations.get("optimizations") instanceof List<?> list) {
                    for (Object obj : list) {
                        if (obj instanceof Map<?, ?> opt) {
                            y = writeLine(cs, bold, 9, margin + 10, y, (String) opt.get("category"));
                            y = writeLine(cs, italic, 9, margin + 20, y, "Current: " + opt.get("current"));
                            cs.setNonStrokingColor(new Color(79, 70, 229));
                            y = writeLine(cs, regular, 9, margin + 20, y, "Suggestion: " + opt.get("suggestion"));
                            cs.setNonStrokingColor(Color.BLACK);
                            y -= 5;
                        }
                    }
                }
                y -= 10;

                // ── 5. Growth Areas ──────────────────────────────────────────────────
                drawDivider(cs, margin, y, pageWidth - 2 * margin);
                y -= 20;
                y = writeLine(cs, bold, 11, margin, y, "GROWTH AREAS & SUGGESTIONS");
                if (analysis.get("suggestions") instanceof List<?> list) {
                    for (Object item : list) {
                        y = writeLine(cs, regular, 10, margin + 10, y, "•  " + item);
                    }
                }

                // Footer
                cs.setFont(italic, 8);
                cs.setNonStrokingColor(new Color(148, 163, 184));
                cs.beginText();
                cs.newLineAtOffset(margin, 40);
                cs.showText("Generated by AI Resume Analyzer - Pro Edition. Disclaimer: For guidance only.");
                cs.endText();
            }

            document.save(outputStream);
            return outputStream.toByteArray();
        }
    }

    private void drawDivider(PDPageContentStream cs, float x, float y, float width) throws IOException {
        cs.setStrokingColor(new Color(226, 232, 240));
        cs.setLineWidth(1);
        cs.moveTo(x, y);
        cs.lineTo(x + width, y);
        cs.stroke();
    }

    // ── Internal: call the Python AI service ─────────────────────────────────
    private Map<String, Object> callAiService(String path, String fileName,
            byte[] fileBytes, String jobDescription) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        // Send shared secret so AI service can reject unauthorized callers
        headers.set("X-API-Key", aiServiceKey);

        ByteArrayResource resource = new ByteArrayResource(fileBytes) {
            @Override
            public String getFilename() {
                return fileName;
            }
        };

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", resource);
        if (jobDescription != null) {
            body.add("job_description", jobDescription);
        }

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        try {
            String baseUrl = aiServiceUrl;
            // Handle Render internal hostnames vs full URLs
            if (baseUrl != null && !baseUrl.startsWith("http")) {
                baseUrl = "http://" + baseUrl + ":8000";
            }
            String finalUrl = baseUrl + path;
            System.out.println(">>> ResumeService: Calling AI Service at " + finalUrl);

            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    finalUrl,
                    HttpMethod.POST,
                    requestEntity,
                    new ParameterizedTypeReference<Map<String, Object>>() {
                    });

            Map<String, Object> aiResponse = response.getBody();
            System.out.println(
                    ">>> ResumeService: AI Service response: " + (aiResponse != null ? aiResponse.keySet() : "NULL"));
            return aiResponse;
        } catch (org.springframework.web.client.ResourceAccessException e) {

            throw new RuntimeException("AI Service is currently unavailable. Please try again later.");
        } catch (Exception e) {
            throw new RuntimeException("AI Analysis failed: " + e.getMessage());
        }
    }

    // ── Helper for PDFBox line writing ───────────────────────────────────────
    private float writeLine(PDPageContentStream cs, PDType1Font font, float fontSize,
            float x, float y, String text) throws IOException {
        if (y < 60)
            return y;
        cs.beginText();
        cs.setFont(font, fontSize);
        cs.newLineAtOffset(x, y);
        cs.showText(text);
        cs.endText();
        return y - 18;
    }
}
