package kz.qazpost.integration.administrationservice.service;

import kz.qazpost.integration.common.Role;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;

import java.util.List;

public interface RoleService {

    Page<Role> getAll(int page, int size, String code, String desc);

    List<Role> getAll(String code, String description);

    Role getByCode(String code);

    Role save(Role role);

    ResponseEntity<?> bind(String username, String roleCode);

    ResponseEntity<?> unbind(String username, String roleCode);

    ResponseEntity<?> delete(String roleCode);

}
