package com.musaib.resumeanalyzer.controller;

import com.musaib.resumeanalyzer.config.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private com.musaib.resumeanalyzer.repository.UserRepository userRepository;

    @Autowired
    private org.springframework.security.crypto.password.PasswordEncoder passwordEncoder;

    @jakarta.annotation.PostConstruct
    public void initAdmin() {
        if (userRepository.count() == 0) {
            com.musaib.resumeanalyzer.entity.User admin = new com.musaib.resumeanalyzer.entity.User();
            admin.setName("System Admin");
            admin.setEmail("admin@example.com");
            // Default password: admin123 (hashed)
            admin.setPassword(passwordEncoder.encode("admin123"));
            admin.setRole("ADMIN");
            userRepository.save(admin);
            System.out.println(">>> Bootstrap: Default admin user created (admin / admin123)");
        }
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> credentials) {
        String email = credentials.get("username"); // Using username field for email/name
        String password = credentials.get("password");

        // Try find by name or email
        java.util.Optional<com.musaib.resumeanalyzer.entity.User> userOpt = userRepository.findAll().stream()
                .filter(u -> "admin".equals(email) || u.getEmail().equals(email) || u.getName().equals(email))
                .findFirst();

        if (userOpt.isPresent() && passwordEncoder.matches(password, userOpt.get().getPassword())) {
            String token = jwtUtil.generateToken(userOpt.get().getEmail());
            return ResponseEntity.ok(Map.of(
                    "token", token,
                    "username", userOpt.get().getName(),
                    "message", "Login successful"));
        }

        return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .body(Map.of("error", "Invalid credentials"));
    }

    @PostMapping("/validate")
    public ResponseEntity<?> validateToken(
            @RequestHeader(value = "Authorization", required = false) String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            boolean isValid = jwtUtil.isTokenValid(token);
            System.out.println(">>> AuthController: Validation check for token, isValid=" + isValid);
            if (isValid) {
                return ResponseEntity.ok(Map.of("valid", true));
            }
        } else {
            System.out.println(">>> AuthController: No Authorization header in validate request");
        }
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("valid", false));
    }
}
