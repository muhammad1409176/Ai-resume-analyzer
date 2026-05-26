package com.musaib.resumeanalyzer.repository;

import com.musaib.resumeanalyzer.entity.Resume;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface ResumeRepository extends JpaRepository<Resume, Long> {

    @Query("SELECT AVG(r.atsScore) FROM Resume r WHERE r.atsScore IS NOT NULL")
    Double findAverageScore();

    @Query("SELECT MAX(r.atsScore) FROM Resume r WHERE r.atsScore IS NOT NULL")
    Integer findMaxScore();

    @Query("SELECT COUNT(r) FROM Resume r WHERE r.atsScore IS NOT NULL")
    Long countAnalyzed();

    @Query("SELECT r.atsScore FROM Resume r WHERE r.atsScore IS NOT NULL")
    java.util.List<Integer> findAllScores();

    @Query("SELECT r.uploadedAt FROM Resume r WHERE r.uploadedAt IS NOT NULL")
    java.util.List<java.time.LocalDateTime> findAllUploadDates();

}
