package kz.qazpost.integration.administrationservice.controller;

import kz.qazpost.integration.administrationservice.service.AuthService;
import kz.qazpost.integration.common.UserDto;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login/ldap")
    public ResponseEntity<UserDto> loginLdap(@RequestBody Map<String, ?> request) {
        String username = request.get("login").toString();
        String password = request.get("password").toString();
        return authService.login(username, password);
    }

    @GetMapping("/logout")
    public ResponseEntity<String> logoutSuccess() {
        return ResponseEntity.ok("Вы успешно вышли из системы.");
    }
}