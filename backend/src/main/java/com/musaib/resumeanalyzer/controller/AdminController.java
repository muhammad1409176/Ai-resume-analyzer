package com.musaib.resumeanalyzer.controller;

import com.musaib.resumeanalyzer.repository.ResumeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@CrossOrigin(origins = "*")
public class AdminController {

    @Autowired
    private ResumeRepository resumeRepository;

    @GetMapping("/stats")
    public Map<String, Object> getStats() {
        Map<String, Object> stats = new HashMap<>();

        long totalResumes = resumeRepository.count();

        // Placeholder values for now
        double averageScore = 74.0;
        int highestScore = 98;

        stats.put("totalResumes", totalResumes);
        stats.put("averageScore", averageScore);
        stats.put("highestScore", highestScore);
        stats.put("topMissingSkill", "AWS");
        stats.put("topRecommendedRole", "Full Stack Developer");

        return stats;
    }
}