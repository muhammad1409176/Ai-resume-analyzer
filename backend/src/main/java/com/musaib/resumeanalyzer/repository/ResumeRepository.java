package com.musaib.resumeanalyzer.repository;

import com.musaib.resumeanalyzer.entity.Resume;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ResumeRepository extends JpaRepository<Resume, Long> {
}