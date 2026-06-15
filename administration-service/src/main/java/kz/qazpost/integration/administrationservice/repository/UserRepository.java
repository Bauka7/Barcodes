package kz.qazpost.integration.administrationservice.repository;

import kz.qazpost.integration.administrationservice.entities.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    @Query("select u from User u where u.username = :username")
    Optional<User> findByUsername(String username);

    Page<User> findByNameContainingIgnoreCase(String name, Pageable pageable);

    @Query(value = """
            select distinct u
            from User u
            join UserRoles r on r.userId = u.id
            where r.roleCode = :code
            """)
    List<User> findByRole(@Param("code") String code);

}
