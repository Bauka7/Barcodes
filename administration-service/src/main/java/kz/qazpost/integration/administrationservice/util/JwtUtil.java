package kz.qazpost.integration.administrationservice.util;

import jakarta.annotation.PostConstruct;
import kz.qazpost.integration.administrationservice.service.UserService;
import kz.qazpost.integration.common.User;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class JwtUtil {

    private final UserService userService;

    private static JwtUtil INSTANCE;

    @PostConstruct
    public void init() {
        INSTANCE = this;
    }

    public static User extractUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication instanceof JwtAuthenticationToken jwtAuth) {
            Jwt jwt = jwtAuth.getToken();
            String username = jwt.getClaimAsString("preferred_username");
            return INSTANCE.userService.getByUsername(username);
        }
        return null;
    }

    public static String extractUsername() {
        User user = extractUser();
        return user != null ? user.getUsername() : null;
    }

    public static Long extractUserId() {
        User user = extractUser();
        return user != null ? user.getId() : null;
    }

}