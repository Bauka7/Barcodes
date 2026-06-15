package kz.qazpost.integration.administrationservice.service;

import kz.qazpost.integration.common.TokenResponse;
import org.springframework.security.oauth2.core.oidc.OidcUserInfo;

public interface TokenService {

    TokenResponse getToken(String username, String password);

    OidcUserInfo getUserInfo(String accessToken);

}
