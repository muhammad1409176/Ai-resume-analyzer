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
@CrossOrigin(origins = { "http://localhost:3000", "http://localhost:3001" })
public class ResumeController {

    @Autowired
    private ResumeService resumeService;

    @PostMapping("/upload")
    public String uploadResume(@RequestParam("file") MultipartFile file)
            throws IOException {
        return resumeService.uploadResume(file);
    }

    @PostMapping("/upload-and-analyze")
    public Map<String, Object> uploadAndAnalyze(
            @RequestParam("file") MultipartFile file) throws IOException {
        return resumeService.uploadAndAnalyze(file);
    }

    @PostMapping(value = "/match-job", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> matchJob(
            @RequestParam("file") MultipartFile file,
            @RequestParam("jobDescription") String jobDescription) throws IOException {
        return resumeService.matchJob(file, jobDescription);
    }

    @PostMapping("/generate-report")
    public ResponseEntity<byte[]> generateReport(
            @RequestParam("file") MultipartFile file) throws Exception {

        byte[] pdfBytes = resumeService.generatePdfReport(file);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDisposition(
                ContentDisposition.attachment()
                        .filename("resume-analysis-report.pdf")
                        .build());

        return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
    }
}