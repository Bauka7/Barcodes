package kz.qazpost.integration.administrationservice.service.impl;

import kz.qazpost.integration.administrationservice.service.AuthService;
import kz.qazpost.integration.administrationservice.service.TokenService;
import kz.qazpost.integration.administrationservice.service.UserService;
import kz.qazpost.integration.common.TokenResponse;
import kz.qazpost.integration.common.UserDto;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.oauth2.core.oidc.OidcUserInfo;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserService userService;
    private final TokenService tokenService;

    @Override
    public ResponseEntity<UserDto> login(String username, String password) {
        username = username.trim().toLowerCase();
        TokenResponse token = tokenService.getToken(username, password);
        OidcUserInfo userInfo = tokenService.getUserInfo(token.getAccessToken());
        kz.qazpost.integration.common.User currentUser = userService.save(userInfo.getPreferredUsername().toLowerCase(), userInfo.getEmail(), userInfo.getFullName());
        return ResponseEntity.ok(new UserDto(currentUser, token.getAccessToken(), LocalDateTime.now().plusSeconds(token.getExpiresIn())));
    }

}
