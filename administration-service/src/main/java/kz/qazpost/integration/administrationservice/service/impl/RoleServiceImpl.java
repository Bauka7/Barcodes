package kz.qazpost.integration.administrationservice.service.impl;

import kz.qazpost.integration.administrationservice.entities.Role;
import kz.qazpost.integration.administrationservice.entities.User;
import kz.qazpost.integration.administrationservice.entities.UserRoles;
import kz.qazpost.integration.administrationservice.repository.RoleRepository;
import kz.qazpost.integration.administrationservice.repository.UserRepository;
import kz.qazpost.integration.administrationservice.repository.UserRolesRepository;
import kz.qazpost.integration.administrationservice.service.RoleService;
import kz.qazpost.integration.administrationservice.service.UserService;
import kz.qazpost.integration.administrationservice.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Objects;

@Service
@RequiredArgsConstructor
public class RoleServiceImpl implements RoleService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final UserRolesRepository userRolesRepository;
    private final UserService userService;

    @Override
    public Page<kz.qazpost.integration.common.Role> getAll(int page, int size, String code, String description) {
        Pageable pageable = PageRequest.of(page, size);
        Page<Role> rolePage;
        if ((code != null && !code.isEmpty()) || (description != null && !description.isEmpty()))
            rolePage = roleRepository.findByCodeContainingIgnoreCaseOrDescriptionContainingIgnoreCase(code, description, pageable);
        else
            rolePage = roleRepository.findAll(pageable);
        return rolePage.map(this::cast);
    }

    @Override
    public List<kz.qazpost.integration.common.Role> getAll(String code, String description) {
        List<Role> rolePage;
        if ((code != null && !code.isEmpty()) || (description != null && !description.isEmpty()))
            rolePage = roleRepository.findByCodeContainingIgnoreCaseOrDescriptionContainingIgnoreCase(code, description);
        else
            rolePage = roleRepository.findAll();
        return rolePage.stream().map(this::cast).toList();
    }

    @Override
    public kz.qazpost.integration.common.Role getByCode(String code) {
        return roleRepository.findByCode(code).map(this::cast).orElse(null);
    }

    @Override
    public kz.qazpost.integration.common.Role save(kz.qazpost.integration.common.Role role) {
        Role roleEntity = roleRepository.findByCode(role.code).orElse(Role.builder()
                .code(role.code)
                .createdAt(LocalDateTime.now())
                .build());

        roleEntity.setDescription(role.getDescription());
        roleEntity.setCreatedBy(Objects.requireNonNull(JwtUtil.extractUser()).getId());

        return cast(roleRepository.save(roleEntity));
    }

    @Override
    public ResponseEntity<?> bind(String username, String roleCode) {
        User user = userRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("User not found"));
        Role role = roleRepository.findByCode(roleCode).orElseThrow(() -> new RuntimeException("Role not found"));
        List<UserRoles> roles = userRolesRepository.findByUserId(user.getId());
        if (roles.stream().noneMatch(x -> x.getRoleCode().equals(roleCode)))
            userRolesRepository.save(UserRoles.builder()
                    .userId(user.getId())
                    .roleCode(role.getCode())
                    .boundBy(JwtUtil.extractUserId())
                    .bindingDate(LocalDateTime.now())
                    .build());
        return ResponseEntity.ok(userService.getById(user.getId()));
    }

    @Override
    @Transactional
    public ResponseEntity<?> unbind(String username, String roleCode) {
        User user = userRepository.findByUsername(username).orElseThrow(() -> new RuntimeException("User not found"));
        Role role = roleRepository.findByCode(roleCode).orElseThrow(() -> new RuntimeException("Role not found"));
        List<UserRoles> roles = userRolesRepository.findByUserId(user.getId());
        roles.stream().filter(x -> x.getRoleCode().equals(role.getCode())).forEach(x -> userRolesRepository.deleteById(x.getId()));
        return ResponseEntity.ok(userService.getById(user.getId()));
    }

    public ResponseEntity<Void> delete(String roleCode) {
        Role role = roleRepository.findByCode(roleCode).orElseThrow(() -> new RuntimeException("Role not found"));
        List<User> user = userRepository.findByRole(role.code);
        if (user.isEmpty()) {
            roleRepository.delete(role);
            return ResponseEntity.ok().build();
        } else {
            throw new RuntimeException("Cannot delete role, role is bound to user");
        }
    }

    private kz.qazpost.integration.common.Role cast(Role role) {
        return kz.qazpost.integration.common.Role.builder()
                .code(role.getCode())
                .description(role.getDescription())
                .createdAt(LocalDateTime.now())
                .createdBy(role.getCreatedBy())
                .build();
    }

}
