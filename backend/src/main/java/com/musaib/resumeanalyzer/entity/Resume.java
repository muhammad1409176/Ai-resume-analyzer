package com.musaib.resumeanalyzer.entity;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;

@Entity
@Table(name = "resumes")
@Data
public class Resume {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "file_name")
    private String fileName;

    @Column(name = "file_path")
    private String filePath;

    @Column(name = "uploaded_at")
    private LocalDateTime uploadedAt;

    @Column(name = "ats_score")
    private Integer atsScore;

    @ElementCollection
    @CollectionTable(name = "resume_strengths", joinColumns = @JoinColumn(name = "resume_id"))
    @Column(name = "strength")
    private java.util.List<String> strengths;

    @ElementCollection
    @CollectionTable(name = "resume_missing_keywords", joinColumns = @JoinColumn(name = "resume_id"))
    @Column(name = "keyword")
    private java.util.List<String> missingKeywords;

    @ElementCollection
    @CollectionTable(name = "resume_suggestions", joinColumns = @JoinColumn(name = "resume_id"))
    @Column(name = "suggestion")
    private java.util.List<String> suggestions;

    @ElementCollection
    @CollectionTable(name = "resume_career_recommendations", joinColumns = @JoinColumn(name = "resume_id"))
    @Column(name = "recommendation")
    private java.util.List<String> careerRecommendations;
}
