package kz.qazpost.integration.administrationservice.service;

import kz.qazpost.integration.common.UserDto;
import org.springframework.http.ResponseEntity;

public interface AuthService {

    ResponseEntity<UserDto> login(String username, String password);

}
