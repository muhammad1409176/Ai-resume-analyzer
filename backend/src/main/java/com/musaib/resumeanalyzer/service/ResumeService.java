package com.musaib.resumeanalyzer.service;

import com.itextpdf.text.Document;
import com.itextpdf.text.Paragraph;
import com.itextpdf.text.pdf.PdfWriter;
import com.musaib.resumeanalyzer.entity.Resume;
import com.musaib.resumeanalyzer.repository.ResumeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
public class ResumeService {

    private static final String UPLOAD_DIR = System.getProperty("user.dir") + "/uploads";

    private static final String AI_SERVICE_URL = "https://ai-resume-analyzer-ai-iues.onrender.com";

    @Autowired
    private ResumeRepository resumeRepository;

    @Autowired
    private RestTemplate restTemplate;

    // Upload Resume
    public String uploadResume(MultipartFile file) throws IOException {
        Path uploadPath = Paths.get(UPLOAD_DIR);

        if (!Files.exists(uploadPath)) {
            Files.createDirectories(uploadPath);
        }

        String fileName = file.getOriginalFilename();
        Path filePath = uploadPath.resolve(fileName);

        Files.copy(
                file.getInputStream(),
                filePath,
                StandardCopyOption.REPLACE_EXISTING);

        Resume resume = new Resume();
        resume.setFileName(fileName);
        resume.setFilePath(filePath.toString());
        resume.setUploadedAt(LocalDateTime.now());

        resumeRepository.save(resume);

        return fileName;
    }

    // Get All Resumes
    public List<Resume> getAllResumes() {
        return resumeRepository.findAll();
    }

    // Get Resume By ID
    public Resume getResumeById(Long id) {
        return resumeRepository.findById(id).orElse(null);
    }

    // Upload and Analyze Resume
    public Map<String, Object> uploadAndAnalyze(
            MultipartFile file) throws IOException {

        String fileName = uploadResume(file);

        String filePath = System.getProperty("user.dir")
                + "/uploads/"
                + fileName;

        filePath = filePath.replace("\\", "/");

        String url = AI_SERVICE_URL
                + "/analyze?file_path="
                + filePath;

        return restTemplate.getForObject(url, Map.class);
    }

    // Match Resume with Job Description
    public Map<String, Object> matchJob(
            MultipartFile file,
            String jobDescription) throws IOException {

        String fileName = uploadResume(file);

        String filePath = System.getProperty("user.dir")
                + "/uploads/"
                + fileName;

        filePath = filePath.replace("\\", "/");

        String url = AI_SERVICE_URL
                + "/match?file_path="
                + filePath
                + "&job_description="
                + java.net.URLEncoder.encode(
                        jobDescription,
                        java.nio.charset.StandardCharsets.UTF_8);

        return restTemplate.getForObject(url, Map.class);
    }

    // Generate PDF Report
    public byte[] generatePdfReport(
            MultipartFile file) throws Exception {

        // Analyze the resume
        Map<String, Object> analysis = uploadAndAnalyze(file);

        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        Document document = new Document();
        PdfWriter.getInstance(document, outputStream);

        document.open();

        // Title
        document.add(new Paragraph("AI Resume Analysis Report"));
        document.add(new Paragraph(" "));

        // Basic Details
        document.add(new Paragraph(
                "Resume Score: "
                        + analysis.get("score")
                        + "/100"));

        document.add(new Paragraph(
                "Word Count: "
                        + analysis.get("word_count")));

        document.add(new Paragraph(" "));

        // Strengths
        document.add(new Paragraph("Strengths:"));

        if (analysis.get("strengths") != null) {
            for (Object item : (List<?>) analysis.get("strengths")) {
                document.add(new Paragraph("- " + item));
            }
        }

        document.add(new Paragraph(" "));

        // Missing Keywords
        document.add(new Paragraph("Missing Keywords:"));

        Object missing = analysis.get("missing_keywords");

        if (missing == null) {
            missing = analysis.get("missingKeywords");
        }

        if (missing != null) {
            for (Object item : (List<?>) missing) {
                document.add(new Paragraph("- " + item));
            }
        }

        document.add(new Paragraph(" "));

        // Suggestions
        document.add(new Paragraph("Suggestions:"));

        if (analysis.get("suggestions") != null) {
            for (Object item : (List<?>) analysis.get("suggestions")) {
                document.add(new Paragraph("- " + item));
            }
        }

        document.close();

        return outputStream.toByteArray();
    }
}