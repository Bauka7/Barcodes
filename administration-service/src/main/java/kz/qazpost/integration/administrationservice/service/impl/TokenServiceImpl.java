package kz.qazpost.integration.administrationservice.service.impl;

import kz.qazpost.integration.administrationservice.service.TokenService;
import kz.qazpost.integration.common.TokenResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.security.oauth2.core.oidc.OidcUserInfo;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
public class TokenServiceImpl implements TokenService {

    @Value("${keycloak.token-uri}")
    private String tokenUri;
    @Value("${keycloak.client-id}")
    private String clientId;
    @Value("${keycloak.client-secret}")
    private String clientSecret;
    @Value("${keycloak.issuer-uri}")
    private String issuerUri;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public TokenResponse getToken(String username, String password) {
        String tokenEndpoint = issuerUri + "/protocol/openid-connect/token";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));

        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("grant_type", "password");
        form.add("client_id", clientId);
        form.add("client_secret", clientSecret); // если конфиденциальный клиент
        form.add("username", username);
        form.add("password", password);
        form.add("scope", "openid");

        HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(form, headers);

        ResponseEntity<TokenResponse> response = restTemplate.exchange(
                tokenEndpoint,
                HttpMethod.POST,
                request,
                TokenResponse.class
        );

        if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
            throw new RuntimeException("Failed to get token from Keycloak");
        }

        return response.getBody();
    }

    @Override
    public OidcUserInfo getUserInfo(String accessToken) {
        String userInfoEndpoint = issuerUri + "/protocol/openid-connect/userinfo";

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));
        HttpEntity<Void> entity = new HttpEntity<>(headers);

        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                userInfoEndpoint,
                HttpMethod.GET,
                entity,
                new ParameterizedTypeReference<>() {
                }
        );

        Map<String, Object> attributes = response.getBody();
        if (attributes == null) {
            throw new RuntimeException("UserInfo response is empty");
        }

        return new OidcUserInfo(attributes);
    }

}
