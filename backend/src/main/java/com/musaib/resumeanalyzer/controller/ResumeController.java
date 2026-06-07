package com.musaib.resumeanalyzer.controller;

import com.musaib.resumeanalyzer.service.ResumeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;

@RestController
@RequestMapping("/api/resumes")
public class ResumeController {

    @Autowired
    private ResumeService resumeService;

    // ── P1 FIX: Validate file is PDF before processing ───────────────────────
    private void validatePdfFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("No file provided");
        }
        String originalName = file.getOriginalFilename();
        if (originalName == null || !originalName.toLowerCase().endsWith(".pdf")) {
            throw new IllegalArgumentException("Only PDF files are accepted. Found: " + originalName);
        }
        String contentType = file.getContentType();
        System.out.println(
                ">>> ResumeController: Validating file [" + originalName + "] Content-Type: [" + contentType + "]");

        List<String> validTypes = List.of(
                "application/pdf",
                "application/x-pdf",
                "application/acrobat",
                "applications/vnd.pdf",
                "text/pdf",
                "text/x-pdf",
                "application/octet-stream");

        if (contentType != null && !validTypes.contains(contentType)) {
            throw new IllegalArgumentException("Invalid file type [" + contentType + "]. Only PDF is accepted");
        }
    }

    @PostMapping("/upload-and-analyze")
    public Map<String, Object> uploadAndAnalyze(
            @RequestParam("file") MultipartFile file) throws IOException {
        validatePdfFile(file);
        return resumeService.uploadAndAnalyze(file);
    }

    @PostMapping(value = "/match-job", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> matchJob(
            @RequestParam("file") MultipartFile file,
            @RequestParam("jobDescription") String jobDescription) throws IOException {
        validatePdfFile(file);
        // Validate job description input
        if (jobDescription == null || jobDescription.isBlank()) {
            throw new IllegalArgumentException("Job description cannot be empty.");
        }
        if (jobDescription.length() > 5000) {
            throw new IllegalArgumentException("Job description is too long (max 5000 characters).");
        }
        return resumeService.matchJob(file, jobDescription);
    }

    @PostMapping("/generate-report")
    public ResponseEntity<byte[]> generateReport(
            @RequestParam("file") MultipartFile file) throws Exception {
        validatePdfFile(file);
        byte[] pdfBytes = resumeService.generatePdfReport(file);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDisposition(
                ContentDisposition.attachment()
                        .filename("resume-analysis-report.pdf")
                        .build());

        return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
    }

    @PostMapping("/optimize")
    public Map<String, Object> optimize(@RequestParam("file") MultipartFile file) throws IOException {
        validatePdfFile(file);
        return resumeService.optimizeResume(file);
    }

    @PostMapping("/interview-prep")
    public Map<String, Object> interviewPrep(@RequestParam("file") MultipartFile file) throws IOException {
        validatePdfFile(file);
        return resumeService.generateInterviewQuestions(file);
    }

    @PostMapping("/generate-cover-letter")
    public Map<String, Object> generateCoverLetter(
            @RequestParam("file") MultipartFile file,
            @RequestParam("job_description") String jobDescription) throws IOException {
        validatePdfFile(file);
        return resumeService.generateCoverLetter(file, jobDescription);
    }

    // ── Global exception handler for validation and service errors ───────────
    @ExceptionHandler({ IllegalArgumentException.class, RuntimeException.class })
    public ResponseEntity<Map<String, String>> handleErrors(Exception ex) {
        System.err.println(">>> ResumeController Error: " + ex.getMessage());
        HttpStatus status = (ex instanceof IllegalArgumentException) ? HttpStatus.BAD_REQUEST
                : HttpStatus.INTERNAL_SERVER_ERROR;
        return ResponseEntity.status(status).body(Map.of("error", ex.getMessage()));
    }
}
