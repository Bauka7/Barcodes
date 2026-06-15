package kz.qazpost.integration.administrationservice.service;

import org.springframework.data.domain.Page;

public interface UserService {

    Page<kz.qazpost.integration.common.User> getAll(int page, int size, String text);

    kz.qazpost.integration.common.User getById(Long id);

    kz.qazpost.integration.common.User getByUsername(String login);

    kz.qazpost.integration.common.User save(String userName, String email, String fullName);
}
