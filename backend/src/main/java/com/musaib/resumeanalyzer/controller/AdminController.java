package com.musaib.resumeanalyzer.controller;

import com.musaib.resumeanalyzer.entity.Resume;
import com.musaib.resumeanalyzer.repository.ResumeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    @Autowired
    private ResumeRepository resumeRepository;

    @Autowired
    private com.musaib.resumeanalyzer.service.ResumeService resumeService;

    @GetMapping("/stats")
    public Map<String, Object> getStats() {
        System.out.println(">>> AdminController: Received request for /stats");
        Map<String, Object> stats = new HashMap<>();

        java.util.List<Resume> resumes = resumeRepository.findAll();
        long totalResumes = resumes.size();
        Long analyzedResumes = resumeRepository.countAnalyzed();
        Double avgScore = resumeRepository.findAverageScore();
        Integer maxScore = resumeRepository.findMaxScore();

        stats.put("totalResumes", totalResumes);
        stats.put("analyzedResumes", analyzedResumes != null ? analyzedResumes : 0);
        stats.put("averageScore", avgScore != null ? Math.round(avgScore * 10.0) / 10.0 : 0.0);
        stats.put("highestScore", maxScore != null ? maxScore : 0);

        // ── Real Score Distribution ───────────────────────────────────────────
        java.util.List<Integer> scores = resumeRepository.findAllScores();
        int[] distribution = new int[5];
        for (int s : scores) {
            if (s <= 20)
                distribution[0]++;
            else if (s <= 40)
                distribution[1]++;
            else if (s <= 60)
                distribution[2]++;
            else if (s <= 80)
                distribution[3]++;
            else
                distribution[4]++;
        }
        stats.put("scoreDistribution", distribution);

        // ── Portable Monthly Trend (Grouped in Java) ──────────────────────────
        java.util.List<java.time.LocalDateTime> dates = resumeRepository.findAllUploadDates();
        Map<String, Long> trendMap = new HashMap<>();
        java.time.format.DateTimeFormatter formatter = java.time.format.DateTimeFormatter.ofPattern("MMM");
        for (java.time.LocalDateTime d : dates) {
            String month = d.format(formatter);
            trendMap.put(month, trendMap.getOrDefault(month, 0L) + 1);
        }
        stats.put("monthlyTrend", trendMap);

        // ── Real Skill Gap Analytics ──────────────────────────────────────────
        Map<String, Integer> skillCounts = new HashMap<>();
        for (Resume r : resumes) {
            if (r.getMissingKeywords() != null) {
                for (String k : r.getMissingKeywords()) {
                    if (k != null && !k.isEmpty()) {
                        skillCounts.put(k, skillCounts.getOrDefault(k, 0) + 1);
                    }
                }
            }
        }

        java.util.List<Map<String, Object>> topSkills = skillCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(5)
                .map(e -> {
                    Map<String, Object> m = new HashMap<>();
                    m.put("name", e.getKey());
                    m.put("value", e.getValue());
                    return m;
                })
                .toList();
        stats.put("topMissingSkills", topSkills);

        if (!topSkills.isEmpty()) {
            stats.put("topMissingSkill", topSkills.get(0).get("name"));
        }

        // ── Real Role Aggregation ─────────────────────────────────────────────
        Map<String, Integer> roleCounts = new HashMap<>();
        for (Resume r : resumes) {
            if (r.getCareerRecommendations() != null) {
                for (String role : r.getCareerRecommendations()) {
                    roleCounts.put(role, roleCounts.getOrDefault(role, 0) + 1);
                }
            }
        }
        String topRole = roleCounts.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse("Software Engineer");
        stats.put("topRecommendedRole", topRole);

        return stats;
    }

    @org.springframework.web.bind.annotation.DeleteMapping("/resumes/{id}")
    public org.springframework.http.ResponseEntity<?> deleteResume(
            @org.springframework.web.bind.annotation.PathVariable Long id) {
        try {
            resumeService.deleteResume(id);
            return org.springframework.http.ResponseEntity.ok(Map.of("message", "Resume deleted successfully"));
        } catch (java.io.IOException e) {
            return org.springframework.http.ResponseEntity.status(500)
                    .body(Map.of("error", "Failed to delete file: " + e.getMessage()));
        }
    }
}
