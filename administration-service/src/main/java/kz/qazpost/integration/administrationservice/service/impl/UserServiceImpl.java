package kz.qazpost.integration.administrationservice.service.impl;

import kz.qazpost.integration.administrationservice.repository.RoleRepository;
import kz.qazpost.integration.common.Role;
import kz.qazpost.integration.administrationservice.entities.User;
import kz.qazpost.integration.administrationservice.repository.UserRepository;
import kz.qazpost.integration.administrationservice.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;

    @Override
    public Page<kz.qazpost.integration.common.User> getAll(int page, int size, String text) {
        Pageable pageable = PageRequest.of(page, size);
        Page<User> userPage;
        if (text != null && !text.isEmpty())
            userPage = userRepository.findByNameContainingIgnoreCase(text, pageable);
        else
            userPage = userRepository.findAll(pageable);

        return userPage.map(this::cast);
    }

    @Override
    public kz.qazpost.integration.common.User getById(Long id) {
        return userRepository.findById(id).map(this::cast).orElse(null);
    }

    @Override
    public kz.qazpost.integration.common.User getByUsername(String login) {
        return userRepository.findByUsername(login).map(this::cast).orElse(new kz.qazpost.integration.common.User());
    }

    @Override
    public kz.qazpost.integration.common.User save(String userName, String email, String fullName) {
        User user = userRepository.findByUsername(userName).orElse(User.builder().username(userName).build());
        user.setEmail(email);
        user.setName(fullName);
        return cast(userRepository.save(user));
    }

    private kz.qazpost.integration.common.User cast(User user) {
        List<Role> roles = roleRepository.findAllByUserId(user.getId()).stream().map(x -> Role.builder()
                .code(x.getCode())
                .description(x.getDescription())
                .createdBy(x.getCreatedBy())
                .createdAt(x.getCreatedAt())
                .build()).toList();

        return kz.qazpost.integration.common.User.builder()
                .id(user.getId())
                .name(user.getName())
                .username(user.getUsername())
                .email(user.getEmail())
                .roles(roles)
                .build();
    }

}
