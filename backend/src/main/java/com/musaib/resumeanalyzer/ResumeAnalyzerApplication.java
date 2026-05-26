package com.musaib.resumeanalyzer;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@org.springframework.scheduling.annotation.EnableScheduling
public class ResumeAnalyzerApplication {

	public static void main(String[] args) {
		SpringApplication.run(ResumeAnalyzerApplication.class, args);
	}

}
