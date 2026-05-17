package com.musaib.resumeanalyzer.repository;

import com.musaib.resumeanalyzer.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {
}